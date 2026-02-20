"""Files-commented endpoints for commented file operations."""

import io
import logging
import os
import time
import uuid
from email.utils import formatdate
from typing import Any, BinaryIO, Iterator, cast
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, UploadFile
from fastapi import File as UploadFileField
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.exc import DataError, DBAPIError, IntegrityError
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from api.schemas.files import FileCommentedOut
from api.utils.database import get_db
from api.utils.helpers import (
    _build_default_filename_from_instance_parameter,
    _handle_integrity_error,
    _model_list,
    _model_out,
    _raise_for_dbapi_error,
)
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
_COMMENTED_FILE_DB_ERROR_MAP: tuple[tuple[str, int, str], ...] = (
    ("file not found", 404, "File not found"),
    ("user not found", 404, "User not found"),
)


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
    rows = db.execute(text("SELECT file_type, mimetype FROM workflow.files_accepted")).mappings()
    mapping = {row["file_type"].lower(): row["mimetype"] for row in rows}
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


def _commented_filename_from_s3_uid(s3_uid: str) -> str:
    key_name = s3_uid.rsplit("/", 1)[-1]
    if "_" not in key_name:
        return key_name
    prefix, rest = key_name.split("_", 1)
    is_hex_prefix = len(prefix) == 32 and all(ch in "0123456789abcdefABCDEF" for ch in prefix)
    return rest if is_hex_prefix and rest else key_name


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
    sql = """
        SELECT
            fc.id,
            fc.file_id,
            fc.user_id,
            fc.s3_uid,
            fc.mimetype,
            f.rev_id,
            fc.created_at,
            fc.updated_at,
            fc.created_by,
            fc.updated_by
        FROM workflow.files_commented AS fc
        JOIN workflow.v_files AS f ON f.id = fc.file_id
        WHERE fc.file_id = :file_id
    """
    params: dict[str, Any] = {"file_id": file_id}
    if user_id is not None:
        sql += " AND fc.user_id = :user_id"
        params["user_id"] = user_id
    sql += " ORDER BY fc.id"
    rows = db.execute(text(sql), params).mappings().all()
    normalized_rows = [
        {**row, "filename": _commented_filename_from_s3_uid(row["s3_uid"])} for row in rows
    ]
    return _model_list(FileCommentedOut, normalized_rows)


def insert_commented_file(
    request: Request,
    file_id: int = Form(..., description="File ID to attach the commented file to", examples=[1]),
    user_id: int = Form(..., description="User ID uploading the commented file", examples=[1]),
    file: UploadFile | None = UploadFileField(
        None,
        description=(
            "Optional commented file payload. When omitted, the source file identified by "
            "file_id is copied as the commented file."
        ),
    ),
    db: Session = Depends(get_db),
) -> FileCommentedOut:
    """
    Upload a commented file and attach it to an existing file.

    Args:
        request: Incoming request used for logging the client host.
        file_id: The file ID to attach the commented file to.
        user_id: The user ID uploading the commented file.
        file: Optional uploaded file (multipart form data).

    Returns:
        Newly created commented file record with metadata.

    Raises:
        HTTPException: 400 if filename is missing, too long, or file is empty.
        HTTPException: 404 if file or user not found.
        HTTPException: 413 if file exceeds size limit.
    """
    try:
        file_row = (
            db.execute(
                text(
                    """
                    SELECT
                        f.id,
                        f.filename,
                        f.s3_uid,
                        f.mimetype,
                        f.rev_id,
                        r.transmital_current_revision,
                        d.doc_name_unique,
                        d.voided,
                        p.project_name
                    FROM workflow.v_files AS f
                    JOIN workflow.v_document_revisions AS r ON r.rev_id = f.rev_id
                    JOIN workflow.v_documents AS d ON d.doc_id = r.doc_id
                    LEFT JOIN workflow.projects AS p ON p.project_id = d.project_id
                    WHERE f.id = :file_id
                    """
                ),
                {"file_id": file_id},
            )
            .mappings()
            .one_or_none()
        )
    except DataError:
        db.rollback()
        file_row = None
    if not file_row or file_row["voided"]:
        raise HTTPException(status_code=404, detail="File not found")

    user_exists = db.execute(
        text("SELECT user_id FROM workflow.users WHERE user_id = :user_id"),
        {"user_id": user_id},
    ).scalar_one_or_none()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    content_type = file_row["mimetype"]
    filename = file_row["filename"]
    stream: BinaryIO | None = None
    size = None
    copy_from_source = file is None

    if file is not None:
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
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File type '.{file_extension}' is not accepted. Allowed types: Word, Excel, "
                    "PDF, AutoCAD."
                ),
            )
        _validate_mimetype(file_extension, content_type, accepted_mimetype)
        if content_type.lower() != file_row["mimetype"].lower():
            raise HTTPException(
                status_code=415,
                detail=(
                    "Commented file content type does not match original file. "
                    f"Expected '{file_row['mimetype']}'."
                ),
            )

        stream = cast(BinaryIO, file.file)
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

    project_name = file_row["project_name"]
    doc_name = file_row["doc_name_unique"]
    transmital_current_revision = file_row["transmital_current_revision"]
    filename_for_object_key = _build_default_filename_from_instance_parameter(
        db,
        parameter_name="file_name_com_conv",
        fallback_filename=file_row["filename"],
        document_name=file_row["doc_name_unique"],
    )
    object_key = _build_file_object_key(
        project_name=project_name,
        doc_name_unique=doc_name or "doc_unknown",
        transmital_current_revision=transmital_current_revision,
        unique_id=uuid.uuid4().hex,
        filename=filename_for_object_key,
    )

    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    if not _minio_with_retry("bucket_exists", endpoint, lambda: client.bucket_exists(bucket)):
        _minio_with_retry("make_bucket", endpoint, lambda: client.make_bucket(bucket))
    try:
        if copy_from_source:
            try:
                from minio.commonconfig import CopySource
            except ImportError as exc:
                raise HTTPException(
                    status_code=500,
                    detail="MinIO client library not installed; install dependencies.",
                ) from exc

            _minio_with_retry(
                "copy_object",
                endpoint,
                lambda: client.copy_object(
                    bucket,
                    object_key,
                    CopySource(bucket, file_row["s3_uid"]),
                ),
            )
        else:
            if stream is None:
                raise HTTPException(status_code=500, detail="Internal Server Error")
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
        logger.exception("MinIO create/copy failed for commented file key %s", object_key)
        raise

    try:
        new_file = (
            db.execute(
                text(
                    """
                    SELECT
                        id,
                        file_id,
                        user_id,
                        s3_uid,
                        mimetype,
                        created_at,
                        updated_at,
                        created_by,
                        updated_by
                    FROM workflow.create_file_commented(
                        :file_id,
                        :user_id,
                        :s3_uid,
                        :mimetype
                    )
                    """
                ),
                {
                    "file_id": file_id,
                    "user_id": user_id,
                    "s3_uid": object_key,
                    "mimetype": content_type,
                },
            )
            .mappings()
            .one()
        )
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
    except DBAPIError as err:
        db.rollback()
        _raise_for_dbapi_error(err, _COMMENTED_FILE_DB_ERROR_MAP)

    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "Commented file uploaded file_id=%s user_id=%s id=%s client=%s",
        file_id,
        user_id,
        new_file["id"],
        client_host,
    )
    response_payload = {
        "id": new_file["id"],
        "file_id": file_id,
        "user_id": user_id,
        "s3_uid": new_file["s3_uid"],
        "filename": filename_for_object_key,
        "mimetype": new_file["mimetype"],
        "rev_id": file_row["rev_id"],
        "created_at": new_file["created_at"],
        "updated_at": new_file["updated_at"],
        "created_by": new_file["created_by"],
        "updated_by": new_file["updated_by"],
    }
    return _model_out(FileCommentedOut, response_payload)


def delete_commented_file(
    commented_file_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a commented file.

    Removes a commented file from both the MinIO object storage and the database.

    Args:
        commented_file_id: Commented file ID to delete.
        request: Incoming request used for logging the client host.

    Raises:
        HTTPException: 404 if commented file not found.
    """
    file_row = (
        db.execute(
            text("SELECT id, s3_uid FROM workflow.files_commented WHERE id = :id"),
            {"id": commented_file_id},
        )
        .mappings()
        .one_or_none()
    )
    if not file_row:
        raise HTTPException(status_code=404, detail="Commented file not found")

    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    try:
        _minio_with_retry(
            "remove_object",
            endpoint,
            lambda: client.remove_object(bucket, file_row["s3_uid"]),
        )
        logger.info(
            "MinIO delete succeeded commented_id=%s s3_uid=%s",
            file_row["id"],
            file_row["s3_uid"],
        )
    except HTTPException:
        logger.exception(
            "MinIO delete failed for commented_id=%s s3_uid=%s",
            file_row["id"],
            file_row["s3_uid"],
        )
        raise

    try:
        db.execute(
            text("SELECT workflow.delete_file_commented(:id)"),
            {"id": commented_file_id},
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "DB delete failed after MinIO delete commented_id=%s s3_uid=%s",
            file_row["id"],
            file_row["s3_uid"],
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "Commented file deleted id=%s s3_uid=%s client=%s",
        file_row["id"],
        file_row["s3_uid"],
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
    summary="Create a commented file.",
    description=(
        "Creates a commented file record linked to the file and user. "
        "If file is provided, uploads the payload; otherwise copies the source file by file_id."
    ),
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
    file: UploadFile | None = UploadFileField(None),
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
    return delete_commented_file(id, request, db)


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
    id: int = Query(..., description="Commented file ID to download", examples=[1]),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Download a commented file.

    Streams a commented file from MinIO object storage to the client with proper headers for
    download (Content-Disposition, ETag, Last-Modified).

    Args:
        request: Incoming request used for logging the client host.
        id: The ID of the commented file to download.

    Returns:
        Streaming response with the file content.

    Raises:
        HTTPException: 404 if commented file not found.
    """
    if request.headers.get("range"):
        raise HTTPException(status_code=416, detail="Range requests are not supported")

    file_row = (
        db.execute(
            text(
                """
                SELECT
                    fc.id,
                    fc.s3_uid,
                    fc.mimetype
                FROM workflow.files_commented AS fc
                WHERE fc.id = :id
                """
            ),
            {"id": id},
        )
        .mappings()
        .one_or_none()
    )
    if not file_row:
        raise HTTPException(status_code=404, detail="Commented file not found")

    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "event=commented_download_start commented_id=%s s3_uid=%s client=%s",
        file_row["id"],
        file_row["s3_uid"],
        client_host,
    )
    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    response = _minio_with_retry(
        "get_object",
        endpoint,
        lambda: client.get_object(bucket, file_row["s3_uid"]),
    )
    stat = _minio_with_retry(
        "stat_object",
        endpoint,
        lambda: client.stat_object(bucket, file_row["s3_uid"]),
    )

    filename = _commented_filename_from_s3_uid(file_row["s3_uid"])
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
        file_row["id"],
        file_row["s3_uid"],
        client_host,
    )

    # Prefer stored mimetype; fall back to MinIO stat, then octet-stream.
    mimetype = file_row["mimetype"] or stat.content_type or "application/octet-stream"

    return StreamingResponse(
        _stream_minio(response),
        media_type=mimetype,
        headers=headers,
        background=BackgroundTask(_close_minio_response, response),
    )
