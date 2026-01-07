"""MinIO (S3) storage configuration and utilities."""

import logging
import os
import re
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Callable, TypeVar
from urllib.parse import urlparse

from fastapi import HTTPException

T = TypeVar("T")
_MINIO_TIME_OFFSET_SEC = 0.0
logger = logging.getLogger(__name__)


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


def _apply_minio_time_offset(offset_sec: float) -> None:
    global _MINIO_TIME_OFFSET_SEC
    _MINIO_TIME_OFFSET_SEC = offset_sec
    try:
        from minio import time as minio_time

        try:
            original_utcnow = minio_time._original_utcnow  # type: ignore[attr-defined]
        except AttributeError:
            original_utcnow = minio_time.utcnow
            minio_time._original_utcnow = original_utcnow  # type: ignore[attr-defined]

        def _utcnow() -> datetime:
            return original_utcnow() + timedelta(seconds=_MINIO_TIME_OFFSET_SEC)

        minio_time.utcnow = _utcnow  # type: ignore[assignment]
        try:
            from minio.credentials import providers as minio_providers

            minio_providers.utcnow = _utcnow  # type: ignore[assignment]
        except Exception:
            logger.debug(
                "Unable to override MinIO credential providers time function; "
                "continuing with core time offset only.",
                exc_info=True,
            )
    except Exception:
        logger.exception("Failed to apply MinIO time offset")


def _sync_minio_time(err: Exception) -> bool:
    try:
        from minio.error import S3Error
    except Exception:
        return False
    if not isinstance(err, S3Error):
        return False
    if err.code != "RequestTimeTooSkewed":
        return False
    date_header = err.response.headers.get("Date")
    if not date_header:
        return False
    try:
        server_time = parsedate_to_datetime(date_header)
    except Exception:
        return False
    if server_time.tzinfo is None:
        server_time = server_time.replace(tzinfo=timezone.utc)
    local_time = datetime.now(timezone.utc)
    offset = (server_time - local_time).total_seconds()
    _apply_minio_time_offset(offset)
    logger.warning("Adjusted MinIO time offset by %.2fs due to skew", offset)
    return True


def _minio_with_retry(action: str, endpoint: str, func: Callable[[], T]) -> T:
    retries = int(os.getenv("MINIO_RETRIES", "3"))
    delay = float(os.getenv("MINIO_RETRY_DELAY_SEC", "1"))
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as err:
            if _sync_minio_time(err):
                # Time skew detected and offset adjusted; retry immediately once.
                try:
                    return func()
                except Exception as retry_err:
                    err = retry_err
            if attempt < retries:
                time.sleep(delay)
                continue
            logger.exception("MinIO %s failed after %s attempts: %s", action, retries, err)
            raise HTTPException(
                status_code=502,
                detail=f"MinIO {action} failed; check MINIO_ENDPOINT ({endpoint})",
            ) from err


def _s3_safe_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9.\-\s]", "_", value.strip()).replace("/", "_")[:128]


def _build_file_object_key(
    project_name: str | None,
    doc_name_unique: str,
    transmital_current_revision: str,
    unique_id: str,
    filename: str,
) -> str:
    project_segment = _s3_safe_segment(project_name) if project_name else "unassigned"
    doc_segment = _s3_safe_segment(doc_name_unique) if doc_name_unique else "doc_unknown"
    rev_segment = _s3_safe_segment(transmital_current_revision)
    basename = os.path.basename(filename)
    normalized_name = unicodedata.normalize("NFKC", basename)
    safe_filename = _s3_safe_segment(normalized_name) or "file"
    return f"{project_segment}/{doc_segment}/{rev_segment}/{unique_id}_{safe_filename}"


def _close_minio_response(response) -> None:
    response.close()
    response.release_conn()
