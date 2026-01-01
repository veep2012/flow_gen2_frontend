import pytest
from fastapi import HTTPException

from api.routers.files import _extract_file_extension, _validate_mimetype


def test_extract_file_extension_uppercase() -> None:
    assert _extract_file_extension("FILE.PDF") == "pdf"


def test_extract_file_extension_multiple_dots() -> None:
    assert _extract_file_extension("archive.tar.gz") == "gz"


def test_extract_file_extension_trailing_dot() -> None:
    assert _extract_file_extension("report.") == ""


def test_validate_mimetype_matches() -> None:
    _validate_mimetype("pdf", "application/pdf", "application/pdf")


def test_validate_mimetype_mismatch() -> None:
    with pytest.raises(HTTPException) as exc:
        _validate_mimetype("pdf", "application/octet-stream", "application/pdf")
    assert exc.value.status_code == 415
