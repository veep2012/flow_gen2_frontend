"""MinIO (S3) storage configuration and utilities."""

import os
import re
import time
import unicodedata
from typing import Callable, TypeVar
from urllib.parse import urlparse

from fastapi import HTTPException

T = TypeVar("T")


def _build_minio_client() -> tuple[object, str]:
    try:
        from minio import Minio
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="MinIO client library not installed; install dependencies.",
        ) from exc
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    bucket = os.getenv("MINIO_BUCKET", "flow-default")
    access_key = os.getenv("MINIO_ROOT_USER", "flow_minio")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", "change_me_now")
    secure = os.getenv("MINIO_SECURE", "").lower() in {"1", "true", "yes", "on"}

    if endpoint.startswith(("http://", "https://")):
        parsed = urlparse(endpoint)
        endpoint = parsed.netloc
        secure = parsed.scheme == "https"

    if not endpoint:
        raise HTTPException(status_code=500, detail="MinIO endpoint is not configured")

    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure), bucket


def _minio_with_retry(action: str, endpoint: str, func: Callable[[], T]) -> T:
    import logging

    logger = logging.getLogger(__name__)
    retries = int(os.getenv("MINIO_RETRIES", "3"))
    delay = float(os.getenv("MINIO_RETRY_DELAY_SEC", "1"))
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as err:
            last_err = err
            if attempt < retries:
                time.sleep(delay)
                continue
            logger.exception("MinIO %s failed after %s attempts: %s", action, retries, err)
            raise HTTPException(
                status_code=502,
                detail=f"MinIO {action} failed; check MINIO_ENDPOINT ({endpoint})",
            ) from last_err


def _s3_safe_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9.\-\s]", "_", value.strip()).replace("/", "_")[:128]


def _build_file_object_key(
    project_name: str | None,
    doc_name_unique: str,
    transmittal_current_revision: str,
    unique_id: str,
    filename: str,
) -> str:
    project_segment = _s3_safe_segment(project_name) if project_name else "unassigned"
    doc_segment = _s3_safe_segment(doc_name_unique) if doc_name_unique else "doc_unknown"
    rev_segment = _s3_safe_segment(transmittal_current_revision)
    basename = os.path.basename(filename)
    normalized_name = unicodedata.normalize("NFKC", basename)
    safe_filename = _s3_safe_segment(normalized_name) or "file"
    return f"{project_segment}/{doc_segment}/{rev_segment}/{unique_id}_{safe_filename}"


def _close_minio_response(response) -> None:
    response.close()
    response.release_conn()
