from api.main import _build_file_object_key, _s3_safe_segment


def test_s3_safe_segment_replaces_slashes_and_trims() -> None:
    assert _s3_safe_segment("  Project/Alpha  ") == "Project_Alpha"


def test_build_file_object_key_with_unassigned_project() -> None:
    key = _build_file_object_key(
        project_name=None,
        doc_name_unique="Doc/Name",
        transmittal_current_revision="IFC/1",
        unique_id="abc123",
        filename="report.pdf",
    )
    assert key == "unassigned/Doc_Name/IFC_1/abc123_report.pdf"


def test_build_file_object_key_strips_filename_path() -> None:
    key = _build_file_object_key(
        project_name="Project X",
        doc_name_unique="DOC-001",
        transmittal_current_revision="A",
        unique_id="xyz789",
        filename="uploads/report.txt",
    )
    assert key == "Project X/DOC-001/A/xyz789_report.txt"
