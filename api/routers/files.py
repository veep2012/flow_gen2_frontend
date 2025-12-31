"""Files endpoints for file upload and download operations."""

import os
import uuid
from email.utils import formatdate

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Query, Request, UploadFile
from fastapi import File as UploadFileField
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from api.db.models import Doc, DocRevision, File, Project
from api.schemas.files import FileDelete, FileOut, FileUpdate
from api.utils.database import get_db
from api.utils.helpers import _example_for, _handle_integrity_error, _model_list, _model_out
from api.utils.minio import (
    _build_file_object_key,
    _build_minio_client,
    _close_minio_response,
    _minio_with_retry,
)
from api.utils.responses import COMMON_RESPONSES

router = APIRouter(prefix="/api/v1/files", tags=["files"])


@router.get(
    "/list",
    summary="List all files for a specific revision.",
    description="Returns a list of all files associated with the specified document revision.",
    operation_id="list_files_for_revision",
    tags=["files"],
    response_model=list[FileOut],
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
def list_files_for_revision(
    rev_id: int = Query(..., description="Revision ID to filter files by"),
    db: Session = Depends(get_db),
) -> list[FileOut]:
    """
    List all files for a specific revision.

    Returns a list of all files associated with the specified document revision.

    Args:
        rev_id: The revision ID to filter files by.

    Returns:
        List of files with metadata. If no files exist for the specified revision, an empty list is
        returned.
    """
    files = db.query(File).filter(File.rev_id == rev_id).order_by(File.filename, File.id).all()
    return _model_list(FileOut, files)


@router.post(
    "/insert",
    summary="Upload a file and attach it to a document revision.",
    description=(
        "Uploads a file to MinIO object storage and creates a database record linking it to the "
        "specified document revision."
    ),
    operation_id="insert_file",
    tags=["files"],
    response_model=FileOut,
    status_code=201,
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
def insert_file(
    request: Request,
    rev_id: int = Form(..., description="Revision ID to attach the file to"),
    file: UploadFile = UploadFileField(...),
    db: Session = Depends(get_db),
) -> FileOut:
    """
    Upload a file and attach it to a document revision.

    Uploads a file to MinIO object storage and creates a database record linking it to the specified
    document revision.

    Args:
        request: Incoming request used for logging the client host.
        rev_id: The revision ID to attach the file to.
        file: The uploaded file (multipart form data).

    Returns:
        Newly created file record with metadata.

    Raises:
        HTTPException: 400 if filename is missing, too long, or file is empty.
        HTTPException: 404 if revision not found.
        HTTPException: 413 if file exceeds size limit.
    """
    revision = db.get(DocRevision, rev_id)
    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    filename = os.path.basename(file.filename)
    if len(filename) > 90:
        raise HTTPException(status_code=400, detail="Filename too long (max 90 chars)")

    content_type = file.content_type or "application/octet-stream"
    stream = file.file
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

    doc = revision.doc
    project_name = doc.project.project_name if doc and doc.project else None
    doc_name = doc.doc_name_unique if doc else f"doc_{revision.doc_id}"
    object_key = _build_file_object_key(
        project_name=project_name,
        doc_name_unique=doc_name,
        transmittal_current_revision=revision.transmittal_current_revision,
        unique_id=uuid.uuid4().hex,
        filename=filename,
    )
    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    if not _minio_with_retry("bucket_exists", endpoint, lambda: client.bucket_exists(bucket)):
        _minio_with_retry("make_bucket", endpoint, lambda: client.make_bucket(bucket))
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

    new_file = File(
        filename=filename,
        s3_uid=object_key,
        mimetype=content_type,
        rev_id=rev_id,
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
            logger.exception("Failed to cleanup MinIO object after DB error")
        _handle_integrity_error("Failed to create file record", err, "insert_file")

    db.refresh(new_file)
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "File uploaded rev_id=%s file_id=%s filename=%s client=%s",
        rev_id,
        new_file.id,
        filename,
        client_host,
    )
    return _model_out(FileOut, new_file)


@router.put(
    "/update",
    summary="Update file metadata.",
    description=(
        "Updates the filename of an existing file record (does not update the actual file "
        "content)."
    ),
    operation_id="update_file",
    tags=["files"],
    response_model=FileOut,
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
def update_file(
    payload: FileUpdate = Body(..., examples=_example_for(FileUpdate)),
    db: Session = Depends(get_db),
) -> FileOut:
    """
    Update file metadata.

    Updates the filename of an existing file record (does not update the actual file content).

    Args:
        payload: File update data including file id and new filename.

    Returns:
        Updated file record.

    Raises:
        HTTPException: 400 if filename is empty or too long.
        HTTPException: 404 if file not found.
    """
    filename = payload.filename.strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    if len(filename) > 90:
        raise HTTPException(status_code=400, detail="Filename too long (max 90 chars)")

    file_row = db.get(File, payload.id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    file_row.filename = filename
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to update file", err, "update_file")

    db.refresh(file_row)
    return _model_out(FileOut, file_row)


@router.delete(
    "/delete",
    summary="Delete a file.",
    description="Removes a file from both the MinIO object storage and the database.",
    operation_id="delete_file",
    tags=["files"],
    status_code=204,
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
def delete_file(
    request: Request,
    payload: FileDelete = Body(..., examples=_example_for(FileDelete)),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a file.

    Removes a file from both the MinIO object storage and the database.

    Args:
        payload: File deletion data including file id.
        request: Incoming request used for logging the client host.

    Raises:
        HTTPException: 404 if file not found.
    """
    file_row = db.get(File, payload.id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    client, bucket = _build_minio_client()
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    _minio_with_retry(
        "remove_object",
        endpoint,
        lambda: client.remove_object(bucket, file_row.s3_uid),
    )

    db.delete(file_row)
    db.commit()
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "File deleted file_id=%s s3_uid=%s client=%s",
        payload.id,
        file_row.s3_uid,
        client_host,
    )


@router.get(
    "/download",
    summary="Download a file.",
    description=(
        "Streams a file from MinIO object storage to the client with proper headers for download "
        "(Content-Disposition, ETag, Last-Modified)."
    ),
    operation_id="download_file",
    tags=["files"],
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
def download_file(
    request: Request,
    file_id: int = Query(..., description="File ID to download"),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    Download a file.

    Streams a file from MinIO object storage to the client with proper headers for download
    (Content-Disposition, ETag, Last-Modified).

    Args:
        request: Incoming request used for logging the client host.
        file_id: The ID of the file to download.

    Returns:
        Streaming response with the file content.

    Raises:
        HTTPException: 404 if file not found.
    """
    file_row = db.get(File, file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

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

    safe_name = (
        file_row.filename.replace('"', "'")
        .replace("\r", "")
        .replace("\n", "")
        .encode("latin-1", "ignore")
        .decode("latin-1")
    )
    quoted_name = quote(file_row.filename)
    headers = {
        "Content-Disposition": (
            "attachment; filename=\"{}\"; filename*=UTF-8''{}".format(
                safe_name,
                quoted_name,
            )
        )
    }
    if stat.etag:
        etag = stat.etag.strip('"')
        headers["ETag"] = f'"{etag}"'
    if stat.last_modified:
        headers["Last-Modified"] = formatdate(stat.last_modified.timestamp(), usegmt=True)
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "File download file_id=%s s3_uid=%s client=%s",
        file_row.id,
        file_row.s3_uid,
        client_host,
    )
    return StreamingResponse(
        response,
        media_type=file_row.mimetype or "application/octet-stream",
        headers=headers,
        background=BackgroundTask(_close_minio_response, response),
    )


