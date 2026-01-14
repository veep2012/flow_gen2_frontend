"""Files-commented endpoints for commented file operations."""

import io
import logging
import os
import time
import uuid
from email.utils import formatdate
from typing import Any, BinaryIO, Iterator, cast
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query, Request, UploadFile
from fastapi import File as UploadFileField
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from api.db.models import File, FileAccepted, FileCommented, User
from api.schemas.files import FileCommentedDelete, FileCommentedOut
from api.utils.database import get_db
from api.utils.helpers import _example_for, _handle_integrity_error, _model_list, _model_out
from api.utils.minio import (
    _build_file_object_key,
    _build_minio_client,
    _close_minio_response,
    _minio_with_retry,
)

router = APIRouter(prefix="/api/v1/files/commented", tags=["files-commented"])

logger = logging.getLogger(__name__)

_ACCEPTED_TYPES_CACHE: dict[str, str] = {}
_ACCEPTED_TYPES_CACHE_AT = 0.0


class _PrefixedStream:
    def __init__(self, prefix: bytes, stream) -> None:
        self._prefix = io.BytesIO(prefix)
        self._stream = stream

    def read(self, size: int = -1) -> bytes:
        if size == 0:
            return b""
        prefix_data = self._prefix.read(size)
        if size < 0:
            return prefix_data + self._stream.read()
        if len(prefix_data) < size:
            return prefix_data + self._stream.read(size - len(prefix_data))
        return prefix_data

    def close(self) -> None:
        self._stream.close()


def _stream_minio(response, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
    while True:
        chunk = response.read(chunk_size)
        if not chunk:
            break
        yield chunk


def _parse_accepted_file_mime_map() -> dict[str, str]:
    raw = os.getenv("ACCEPTED_FILE_MIME_MAP", "")
    mapping: dict[str, str] = {}
    if not raw:
        return mapping
    for entry in raw.split(","):
        if "=" not in entry:
            continue
        ext, mime = entry.split("=", 1)
        ext = ext.strip().lstrip(".").lower()
        mime = mime.strip()
        if ext and mime:
            mapping[ext] = mime
    return mapping


def _load_accepted_types(db: Session) -> dict[str, str]:
    mapping = {row.file_type.lower(): row.mimetype for row in db.query(FileAccepted).all()}
    mapping.update(_parse_accepted_file_mime_map())
    return mapping


def _get_cached_accepted_types(db: Session) -> dict[str, str]:
    ttl_sec = int(os.getenv("ACCEPTED_FILE_TYPES_TTL_SEC", "300"))
    now = time.time()
    global _ACCEPTED_TYPES_CACHE_AT
    if _ACCEPTED_TYPES_CACHE and ttl_sec > 0 and (now - _ACCEPTED_TYPES_CACHE_AT) < ttl_sec:
        return _ACCEPTED_TYPES_CACHE
    try:
        _ACCEPTED_TYPES_CACHE.update(_load_accepted_types(db))
        _ACCEPTED_TYPES_CACHE_AT = now
    except Exception:
        logger.exception("Failed to refresh accepted file types cache")
    return _ACCEPTED_TYPES_CACHE


def _extract_file_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def _validate_mimetype(file_extension: str, content_type: str, expected_mimetype: str) -> None:
    if content_type.lower() != expected_mimetype.lower():
        raise HTTPException(
            status_code=415,
            detail=(
                "File content type does not match accepted type for "
                f"'.{file_extension}'. Expected '{expected_mimetype}'."
            ),
        )


def _handle_commented_file_integrity_error(err: IntegrityError) -> None:
    constraint = None
    orig = getattr(err, "orig", None)
    if orig is not None:
        constraint = getattr(getattr(orig, "diag", None), "constraint_name", None)
    if constraint == "files_commented_file_id_user_id_key":
        raise HTTPException(
            status_code=400,
            detail="Commented file already exists for this file and user.",
        )
    _handle_integrity_error("Failed to create commented file record", err, "insert_commented_file")


@router.get(
    "/list",
    summary="List all commented files for a specific file.",
    description=(
        "Returns a list of all commented files associated with the specified file ID. "
        "Optionally filter by user ID."
    ),
    operation_id="list_commented_files_for_file",
    tags=["files-commented"],
    response_model=list[FileCommentedOut],
    responses={
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Bad Request",
                    },
                },
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not Found",
                    },
                },
            },
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": (
                        {
                            "detail": [
                                {
                                    "loc": ["body", "field"],
                                    "msg": "Field required",
                                    "type": "missing",
                                }
                            ]
                        }
                    ),
                },
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal Server Error",
                    },
                },
            },
        },
    },
)
def list_commented_files_for_file(
    file_id: int = Query(
        ..., gt=0, description="File ID to filter commented files by", examples=[1]
    ),
    user_id: int | None = Query(
        None, gt=0, description="Optional User ID to filter by", examples=[1]
    ),
    db: Session = Depends(get_db),
) -> list[FileCommentedOut]:
    """
    List all commented files for a specific file.

    Returns a list of all commented files associated with the specified file ID.
    Optionally filter by user ID.

    Args:
        file_id: The file ID to filter commented files by (mandatory).
        user_id: The user ID to filter by (optional).

    Returns:
        List of commented files with metadata. If no commented files exist for the specified
        file, an empty list is returned.
    """
    query = (
        db.query(FileCommented, File.filename, File.mimetype, File.rev_id)
        .join(File, FileCommented.file_id == File.id)
        .filter(FileCommented.file_id == file_id)
    )
    if user_id is not None:
        query = query.filter(FileCommented.user_id == user_id)
    rows = query.order_by(FileCommented.id).all()
    files = [
        {
            "id": file_row.id,
            "file_id": file_row.file_id,
            "user_id": file_row.user_id,
            "s3_uid": file_row.s3_uid,
            "filename": filename,
            "mimetype": mimetype,
            "rev_id": rev_id,
        }
        for file_row, filename, mimetype, rev_id in rows
    ]
    return _model_list(FileCommentedOut, files)


def insert_commented_file(
    request: Request,
    file_id: int = Form(..., description="File ID to attach the commented file to", examples=[1]),
    user_id: int = Form(..., description="User ID uploading the commented file", examples=[1]),
    file: UploadFile = UploadFileField(...),
    db: Session = Depends(get_db),
) -> FileCommentedOut:
    """
    Upload a commented file and attach it to an existing file.

    Args:
        request: Incoming request used for logging the client host.
        file_id: The file ID to attach the commented file to.
        user_id: The user ID uploading the commented file.
        file: The uploaded file (multipart form data).

    Returns:
        Newly created commented file record with metadata.

    Raises:
        HTTPException: 400 if filename is missing, too long, or file is empty.
        HTTPException: 404 if file or user not found.
        HTTPException: 413 if file exceeds size limit.
    """
    file_row = db.get(File, file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        user_row = db.get(User, user_id)
    except DataError:
        db.rollback()
        raise HTTPException(status_code=404, detail="User not found")
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    filename = os.path.basename(file.filename)
    if len(filename) > 90:
        raise HTTPException(status_code=400, detail="Filename too long (max 90 chars)")

    file_extension = _extract_file_extension(filename)
    if not file_extension:
        raise HTTPException(
            status_code=400,
            detail="File must have an extension. Allowed types: Word, Excel, PDF, AutoCAD.",
        )

    content_type = file.content_type or "application/octet-stream"
    accepted_types = _get_cached_accepted_types(db)
    accepted_mimetype = accepted_types.get(file_extension)
    if not accepted_mimetype:
        accepted_file = (
            db.query(FileAccepted).filter(FileAccepted.file_type == file_extension).first()
        )
        if not accepted_file:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File type '.{file_extension}' is not accepted. Allowed types: Word, Excel, "
                    "PDF, AutoCAD."
                ),
            )
        accepted_mimetype = accepted_file.mimetype
        accepted_types[file_extension] = accepted_mimetype
    _validate_mimetype(file_extension, content_type, accepted_mimetype)
    if content_type.lower() != file_row.mimetype.lower():
        raise HTTPException(
            status_code=415,
            detail=(
                "Commented file content type does not match original file. "
                f"Expected '{file_row.mimetype}'."
            ),
        )

    stream: BinaryIO = cast(BinaryIO, file.file)
    size = None
    if hasattr(stream, "seekable") and stream.seekable():
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(0)
        if size <= 0:
            raise HTTPException(status_code=400, detail="File is empty")
        max_size_mb = int(os.getenv("MAX_UPLOAD_SIZE_MB", "128"))
        max_size_bytes = max_size_mb * 1024 * 1024
        if max_size_mb > 0 and size > max_size_bytes:
            raise HTTPException(status_code=413, detail="File exceeds upload size limit")
    else:
        peek = stream.read(1)
        if not peek:
            raise HTTPException(status_code=400, detail="File is empty")
        stream = cast(BinaryIO, _PrefixedStream(peek, stream))

    revision = file_row.revision
    doc = revision.doc if revision else None
    project_name = doc.project.project_name if doc and doc.project else None
    doc_name = doc.doc_name_unique if doc else f"doc_{revision.doc_id}" if revision else None
    transmital_current_revision = (
        revision.transmital_current_revision if revision else "rev_unknown"
    )
    object_key = _build_file_object_key(
        project_name=project_name,
        doc_name_unique=doc_name or "doc_unknown",
        transmital_current_revision=transmital_current_revision,
        unique_id=uuid.uuid4().hex,
        filename=filename,
    )

    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    if not _minio_with_retry("bucket_exists", endpoint, lambda: client.bucket_exists(bucket)):
        _minio_with_retry("make_bucket", endpoint, lambda: client.make_bucket(bucket))
    try:
        if size is None:
            _minio_with_retry(
                "put_object",
                endpoint,
                lambda: client.put_object(
                    bucket,
                    object_key,
                    stream,
                    length=-1,
                    part_size=10 * 1024 * 1024,
                    content_type=content_type,
                ),
            )
        else:
            _minio_with_retry(
                "put_object",
                endpoint,
                lambda: client.put_object(
                    bucket, object_key, stream, length=size, content_type=content_type
                ),
            )
    except HTTPException:
        logger.exception("MinIO upload failed for commented file key %s", object_key)
        raise

    new_file = FileCommented(
        file_id=file_id,
        user_id=user_id,
        s3_uid=object_key,
        mimetype=content_type,
    )
    db.add(new_file)
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        try:
            _minio_with_retry(
                "remove_object",
                endpoint,
                lambda: client.remove_object(bucket, object_key),
            )
        except HTTPException:
            logger.exception("Failed to cleanup MinIO object after DB error: %s", object_key)
        _handle_commented_file_integrity_error(err)

    db.refresh(new_file)
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "Commented file uploaded file_id=%s user_id=%s id=%s client=%s",
        file_id,
        user_id,
        new_file.id,
        client_host,
    )
    response_payload = {
        "id": new_file.id,
        "file_id": file_id,
        "user_id": user_id,
        "s3_uid": new_file.s3_uid,
        "filename": file_row.filename,
        "mimetype": file_row.mimetype,
        "rev_id": file_row.rev_id,
    }
    return _model_out(FileCommentedOut, response_payload)


def delete_commented_file(
    request: Request,
    payload: FileCommentedDelete = Body(..., openapi_examples=_example_for(FileCommentedDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a commented file.

    Removes a commented file from both the MinIO object storage and the database.

    Args:
        payload: Commented file deletion data including id.
        request: Incoming request used for logging the client host.

    Raises:
        HTTPException: 404 if commented file not found.
    """
    file_row = db.get(FileCommented, payload.id)
    if not file_row:
        raise HTTPException(status_code=404, detail="Commented file not found")

    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    try:
        _minio_with_retry(
            "remove_object",
            endpoint,
            lambda: client.remove_object(bucket, file_row.s3_uid),
        )
        logger.info(
            "MinIO delete succeeded commented_id=%s s3_uid=%s",
            file_row.id,
            file_row.s3_uid,
        )
    except HTTPException:
        logger.exception(
            "MinIO delete failed for commented_id=%s s3_uid=%s",
            file_row.id,
            file_row.s3_uid,
        )
        raise

    try:
        db.delete(file_row)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "DB delete failed after MinIO delete commented_id=%s s3_uid=%s",
            file_row.id,
            file_row.s3_uid,
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "Commented file deleted id=%s s3_uid=%s client=%s",
        payload.id,
        file_row.s3_uid,
        client_host,
    )


# ---------------------------------------------------------------------------
# RESTful aliases (POST collection, DELETE item)
# ---------------------------------------------------------------------------

_REST_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Bad Request",
        "content": {"application/json": {"example": {"detail": "Bad Request"}}},
    },
    404: {
        "description": "Not Found",
        "content": {"application/json": {"example": {"detail": "Not Found"}}},
    },
    422: {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": [
                        {"loc": ["body", "field"], "msg": "Field required", "type": "missing"}
                    ]
                }
            }
        },
    },
    500: {
        "description": "Internal Server Error",
        "content": {"application/json": {"example": {"detail": "Internal Server Error"}}},
    },
}


@router.post(
    "/",
    summary="Upload a commented file.",
    description="Uploads a commented file and creates a record linked to the file and user.",
    operation_id="insert_commented_file_rest",
    tags=["files-commented"],
    response_model=FileCommentedOut,
    status_code=201,
    responses=_REST_RESPONSES,
)
def insert_commented_file_rest(
    request: Request,
    file_id: int = Form(..., description="File ID to attach the commented file to", examples=[1]),
    user_id: int = Form(..., description="User ID uploading the commented file", examples=[1]),
    file: UploadFile = UploadFileField(...),
    db: Session = Depends(get_db),
) -> FileCommentedOut:
    return insert_commented_file(request, file_id, user_id, file, db)


@router.delete(
    "/{id}",
    summary="Delete a commented file.",
    description="Removes a commented file from storage and deletes its database record.",
    operation_id="delete_commented_file_rest",
    tags=["files-commented"],
    status_code=204,
    responses=_REST_RESPONSES,
)
def delete_commented_file_rest(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    return delete_commented_file(request, FileCommentedDelete(id=id), db)


@router.get(
    "/download",
    summary="Download a commented file.",
    description=(
        "Streams a commented file from MinIO object storage to the client with proper headers "
        "for download (Content-Disposition, ETag, Last-Modified)."
    ),
    operation_id="download_commented_file",
    tags=["files-commented"],
    responses={
        200: {
            "description": "File content.",
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"},
                },
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Bad Request",
                    },
                },
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not Found",
                    },
                },
            },
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": (
                        {
                            "detail": [
                                {
                                    "loc": ["body", "field"],
                                    "msg": "Field required",
                                    "type": "missing",
                                }
                            ]
                        }
                    ),
                },
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal Server Error",
                    },
                },
            },
        },
    },
)
def download_commented_file(
    request: Request,
    file_id: int = Query(..., description="Commented file ID to download", examples=[1]),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Download a commented file.

    Streams a commented file from MinIO object storage to the client with proper headers for
    download (Content-Disposition, ETag, Last-Modified).

    Args:
        request: Incoming request used for logging the client host.
        file_id: The ID of the commented file to download.

    Returns:
        Streaming response with the file content.

    Raises:
        HTTPException: 404 if commented file not found.
    """
    if request.headers.get("range"):
        raise HTTPException(status_code=416, detail="Range requests are not supported")

    file_row = db.get(FileCommented, file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="Commented file not found")

    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "event=commented_download_start commented_id=%s s3_uid=%s client=%s",
        file_row.id,
        file_row.s3_uid,
        client_host,
    )
    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    response = _minio_with_retry(
        "get_object",
        endpoint,
        lambda: client.get_object(bucket, file_row.s3_uid),
    )
    stat = _minio_with_retry(
        "stat_object",
        endpoint,
        lambda: client.stat_object(bucket, file_row.s3_uid),
    )

    source_filename = None
    user_acronym = None
    if file_row.file is not None:
        source_filename = file_row.file.filename
    if file_row.user is not None:
        user_acronym = file_row.user.user_acronym

    # Extract filename from s3_uid path as fallback
    filename = source_filename or (
        file_row.s3_uid.split("/")[-1] if "/" in file_row.s3_uid else file_row.s3_uid
    )
    if user_acronym:
        base, ext = os.path.splitext(filename)
        filename = f"{base}_commented_by_{user_acronym}{ext}"
    safe_name = (
        filename.replace('"', "'")
        .replace("\r", "")
        .replace("\n", "")
        .encode("latin-1", "ignore")
        .decode("latin-1")
    )
    quoted_name = quote(filename)
    headers = {
        "Content-Disposition": (
            "attachment; filename=\"{}\"; filename*=UTF-8''{}".format(
                safe_name,
                quoted_name,
            )
        )
    }
    headers["Accept-Ranges"] = "none"
    if stat.etag:
        etag = stat.etag.strip('"')
        headers["ETag"] = f'"{etag}"'
    if stat.last_modified:
        headers["Last-Modified"] = formatdate(stat.last_modified.timestamp(), usegmt=True)

    logger.info(
        "event=commented_download_ready commented_id=%s s3_uid=%s client=%s",
        file_row.id,
        file_row.s3_uid,
        client_host,
    )

    # Prefer stored mimetype; fall back to MinIO stat, then octet-stream.
    mimetype = file_row.mimetype or stat.content_type or "application/octet-stream"

    return StreamingResponse(
        _stream_minio(response),
        media_type=mimetype,
        headers=headers,
        background=BackgroundTask(_close_minio_response, response),
    )
