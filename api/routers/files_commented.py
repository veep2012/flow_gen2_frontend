"""Files-commented endpoints for commented file operations."""

import logging
import os
from email.utils import formatdate
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from api.db.models import FileCommented
from api.schemas.files import FileCommentedDelete, FileCommentedOut, FileCommentedUpdate
from api.utils.database import get_db
from api.utils.helpers import _example_for, _handle_integrity_error, _model_list, _model_out
from api.utils.minio import _build_minio_client, _close_minio_response, _minio_with_retry

router = APIRouter(prefix="/api/v1/files/commented", tags=["files-commented"])

logger = logging.getLogger(__name__)


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
    file_id: int = Query(..., description="File ID to filter commented files by"),
    user_id: int | None = Query(None, description="Optional User ID to filter by"),
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
    query = db.query(FileCommented).filter(FileCommented.file_id == file_id)
    if user_id is not None:
        query = query.filter(FileCommented.user_id == user_id)
    files = query.order_by(FileCommented.id).all()
    return _model_list(FileCommentedOut, files)


@router.put(
    "/update",
    summary="Update commented file metadata.",
    description="Updates the s3_uid of an existing commented file record.",
    operation_id="update_commented_file",
    tags=["files-commented"],
    response_model=FileCommentedOut,
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
def update_commented_file(
    payload: FileCommentedUpdate = Body(..., examples=_example_for(FileCommentedUpdate)),
    db: Session = Depends(get_db),
) -> FileCommentedOut:
    """
    Update commented file metadata.

    Updates the s3_uid of an existing commented file record.

    Args:
        payload: Commented file update data including id and new s3_uid.

    Returns:
        Updated commented file record.

    Raises:
        HTTPException: 404 if commented file not found.
    """
    file_row = db.get(FileCommented, payload.id)
    if not file_row:
        raise HTTPException(status_code=404, detail="Commented file not found")

    file_row.s3_uid = payload.s3_uid
    try:
        db.commit()
    except IntegrityError as err:
        db.rollback()
        _handle_integrity_error("Failed to update commented file", err, "update_commented_file")

    db.refresh(file_row)
    return _model_out(FileCommentedOut, file_row)


@router.delete(
    "/delete",
    summary="Delete a commented file.",
    description="Removes a commented file from both the MinIO object storage and the database.",
    operation_id="delete_commented_file",
    tags=["files-commented"],
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
def delete_commented_file(
    request: Request,
    payload: FileCommentedDelete = Body(..., examples=_example_for(FileCommentedDelete)),
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
    _minio_with_retry(
        "remove_object",
        endpoint,
        lambda: client.remove_object(bucket, file_row.s3_uid),
    )

    db.delete(file_row)
    db.commit()
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "Commented file deleted id=%s s3_uid=%s client=%s",
        payload.id,
        file_row.s3_uid,
        client_host,
    )


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
    file_id: int = Query(..., description="Commented file ID to download"),
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
    file_row = db.get(FileCommented, file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="Commented file not found")

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

    # Extract filename from s3_uid path
    filename = file_row.s3_uid.split("/")[-1] if "/" in file_row.s3_uid else file_row.s3_uid
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
    if stat.etag:
        etag = stat.etag.strip('"')
        headers["ETag"] = f'"{etag}"'
    if stat.last_modified:
        headers["Last-Modified"] = formatdate(stat.last_modified.timestamp(), usegmt=True)

    client_host = request.client.host if request.client else "unknown"
    logger.info(
        "Commented file download id=%s s3_uid=%s client=%s",
        file_row.id,
        file_row.s3_uid,
        client_host,
    )

    # Get mimetype from stat if available, otherwise default
    mimetype = stat.content_type or "application/octet-stream"

    return StreamingResponse(
        response,
        media_type=mimetype,
        headers=headers,
        background=BackgroundTask(_close_minio_response, response),
    )
