import ast
from pathlib import Path

SCENARIO_MAP: dict[str, tuple[str, list[str]]] = {
    "test_audit_fields_document_and_revision": (
        "documentation/test_scenarios/audit_fields_api_test_scenarios.md",
        ["TS-AUD-001"],
    ),
    "test_audit_fields_files_and_commented": (
        "documentation/test_scenarios/audit_fields_api_test_scenarios.md",
        ["TS-AUD-002"],
    ),
    "test_cancel_revision": (
        "documentation/test_scenarios/cancel_delete_api_test_scenarios.md",
        ["TS-CD-001"],
    ),
    "test_cancel_revision_not_cancellable": (
        "documentation/test_scenarios/cancel_delete_api_test_scenarios.md",
        ["TS-CD-002"],
    ),
    "test_cancel_revision_not_found": (
        "documentation/test_scenarios/cancel_delete_api_test_scenarios.md",
        ["TS-CD-003"],
    ),
    "test_delete_document_hard_delete_cascade": (
        "documentation/test_scenarios/cancel_delete_api_test_scenarios.md",
        ["TS-CD-004"],
    ),
    "test_delete_document_void": (
        "documentation/test_scenarios/cancel_delete_api_test_scenarios.md",
        ["TS-CD-005"],
    ),
    "test_delete_document_void_idempotent": (
        "documentation/test_scenarios/cancel_delete_api_test_scenarios.md",
        ["TS-CD-006"],
    ),
    "test_delete_document_concurrent_requests": (
        "documentation/test_scenarios/cancel_delete_api_test_scenarios.md",
        ["TS-CD-007"],
    ),
    "test_delete_document_not_found": (
        "documentation/test_scenarios/cancel_delete_api_test_scenarios.md",
        ["TS-CD-008"],
    ),
    "test_distribution_lists_crud_and_membership": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-DL-001"],
    ),
    "test_distribution_lists_duplicate_name_rejected": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-DL-002"],
    ),
    "test_distribution_list_delete_rejected_when_used_by_notification": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-DL-003"],
    ),
    "test_documents_revisions_list": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-001"],
    ),
    "test_documents_revisions_missing_doc": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-002"],
    ),
    "test_documents_revisions_update": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-003"],
    ),
    "test_documents_revisions_update_missing_fields": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-004"],
    ),
    "test_documents_revisions_update_missing_revision": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-005"],
    ),
    "test_documents_revisions_update_rejects_status_change": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-006"],
    ),
    "test_documents_revisions_create": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-007"],
    ),
    "test_documents_revisions_create_rejects_rev_status_id": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-008"],
    ),
    "test_documents_revisions_create_missing_doc": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-009"],
    ),
    "test_documents_revisions_create_missing_required_fields": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-010"],
    ),
    "test_documents_revisions_status_transition_forward": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-011"],
    ),
    "test_documents_revisions_status_transition_back": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-012"],
    ),
    "test_documents_revisions_status_transition_invalid_direction": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-013"],
    ),
    "test_documents_revisions_status_transition_already_final": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-014"],
    ),
    "test_documents_revisions_status_transition_not_revertible": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-015"],
    ),
    "test_files_commented_list": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-001"],
    ),
    "test_files_commented_list_with_user_filter": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-002"],
    ),
    "test_files_commented_list_missing_file_id": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-003"],
    ),
    "test_files_commented_insert_and_download": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-004"],
    ),
    "test_files_commented_insert_duplicate": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-005"],
    ),
    "test_files_commented_delete_nonexistent": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-006"],
    ),
    "test_files_commented_download_nonexistent": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-007"],
    ),
    "test_files_commented_insert_missing_fields": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-008"],
    ),
    "test_files_commented_insert_nonexistent_file_or_user": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-009"],
    ),
    "test_files_commented_insert_mimetype_mismatch": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-010"],
    ),
    "test_files_commented_insert_without_file_copies_source": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-011"],
    ),
    "test_written_comments_crud": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-001"],
    ),
    "test_written_comments_validation": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-002"],
    ),
    "test_written_comments_missing_references": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-003"],
    ),
    "test_written_comments_delete_forbidden_non_author": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-004"],
    ),
    "test_written_comments_update": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-005"],
    ),
    "test_written_comments_update_forbidden_non_author": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-006"],
    ),
    "test_files_crud_and_download": (
        "documentation/test_scenarios/files_api_test_scenarios.md",
        ["TS-F-001"],
    ),
    "test_files_update_rejects_id_in_body": (
        "documentation/test_scenarios/files_api_test_scenarios.md",
        ["TS-F-002"],
    ),
    "test_files_insert_empty_file_rejected": (
        "documentation/test_scenarios/files_api_test_scenarios.md",
        ["TS-F-003"],
    ),
    "test_files_insert_long_filename_rejected": (
        "documentation/test_scenarios/files_api_test_scenarios.md",
        ["TS-F-004"],
    ),
    "test_files_insert_nonexistent_revision": (
        "documentation/test_scenarios/files_api_test_scenarios.md",
        ["TS-F-005"],
    ),
    "test_files_insert_unaccepted_file_type_rejected": (
        "documentation/test_scenarios/files_api_test_scenarios.md",
        ["TS-F-006"],
    ),
    "test_files_insert_accepted_file_type_pdf": (
        "documentation/test_scenarios/files_api_test_scenarios.md",
        ["TS-F-007"],
    ),
    "test_files_insert_no_extension_rejected": (
        "documentation/test_scenarios/files_api_test_scenarios.md",
        ["TS-F-008"],
    ),
    "test_files_concurrent_uploads_same_revision": (
        "documentation/test_scenarios/files_api_test_scenarios.md",
        ["TS-F-009"],
    ),
    "test_all_get_endpoints": (
        "documentation/test_scenarios/get_endpoints_api_test_scenarios.md",
        ["TS-GET-001"],
    ),
    "test_notifications_create_list_mark_read_flow": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-NTF-001"],
    ),
    "test_notifications_replace_delete_chain": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-NTF-002"],
    ),
    "test_notifications_replace_forbidden_for_non_sender_non_superuser": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-NTF-003"],
    ),
    "test_notifications_mark_read_rejects_payload_user_field": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-NTF-004"],
    ),
    "test_notifications_create_on_behalf_sender": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-NTF-005"],
    ),
    "test_notifications_create_requires_at_least_one_recipient_target": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-NTF-006"],
    ),
}

TEST_FILES = [
    "tests/api/api/test_audit_fields.py",
    "tests/api/api/test_cancel_delete_endpoints.py",
    "tests/api/api/test_distribution_lists_endpoints.py",
    "tests/api/api/test_documents_revisions_endpoints.py",
    "tests/api/api/test_files_commented_endpoints.py",
    "tests/api/api/test_files_endpoints.py",
    "tests/api/api/test_get_endpoints.py",
    "tests/api/api/test_notifications_endpoints.py",
    "tests/api/api/test_written_comments_endpoints.py",
]


def _discover_test_functions(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            if node.name.endswith("traceability_contract"):
                continue
            names.append(node.name)
    return names


def test_api_test_scenarios_traceability_contract() -> None:
    discovered: set[str] = set()
    for file_path in TEST_FILES:
        path = Path(file_path)
        assert path.exists(), f"Missing test file: {file_path}"
        discovered.update(_discover_test_functions(path))

    mapped = set(SCENARIO_MAP.keys())
    assert discovered == mapped, (
        "Scenario map drift detected. "
        f"Unmapped tests: {sorted(discovered - mapped)}. "
        f"Stale mappings: {sorted(mapped - discovered)}"
    )

    for test_name, (doc_path_str, scenario_ids) in SCENARIO_MAP.items():
        doc_path = Path(doc_path_str)
        assert doc_path.exists(), f"Missing scenario doc for {test_name}: {doc_path_str}"
        text = doc_path.read_text(encoding="utf-8")
        assert test_name in text, f"Missing test mapping in doc {doc_path_str}: {test_name}"
        for scenario_id in scenario_ids:
            assert (
                scenario_id in text
            ), f"Missing scenario ID {scenario_id} for test {test_name} in {doc_path_str}"
