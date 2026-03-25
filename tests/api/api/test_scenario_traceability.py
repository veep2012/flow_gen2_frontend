import ast
from pathlib import Path

SCENARIO_MAP: dict[str, tuple[str, list[str]]] = {
    "test_read_rls_multi_role_scope_union": (
        "documentation/test_scenarios/authorization_read_rls_api_test_scenarios.md",
        ["TS-AUTH-001"],
    ),
    "test_read_rls_fail_closed_for_missing_or_unknown_session_user": (
        "documentation/test_scenarios/authorization_read_rls_api_test_scenarios.md",
        ["TS-AUTH-002"],
    ),
    "test_check_user_permission_fail_closed_inputs": (
        "documentation/test_scenarios/authorization_read_rls_api_test_scenarios.md",
        ["TS-AUTH-003"],
    ),
    "test_current_user_identity_does_not_leak_across_rapid_requests": (
        "documentation/test_scenarios/authorization_read_rls_api_test_scenarios.md",
        ["TS-AUTH-004"],
    ),
    "test_read_rls_rejects_unsupported_scope_types": (
        "documentation/test_scenarios/authorization_read_rls_api_test_scenarios.md",
        ["TS-AUTH-005"],
    ),
    "test_audit_fields_document_and_revision": (
        "documentation/test_scenarios/audit_fields_api_test_scenarios.md",
        ["TS-AUD-001"],
    ),
    "test_audit_fields_files_and_commented": (
        "documentation/test_scenarios/audit_fields_api_test_scenarios.md",
        ["TS-AUD-002"],
    ),
    "test_audit_fields_core_schema_contract": (
        "documentation/test_scenarios/audit_fields_api_test_scenarios.md",
        ["TS-AUD-003"],
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
    "test_create_document_succeeds_when_auto_dl_name_already_exists": (
        "documentation/test_scenarios/cancel_delete_api_test_scenarios.md",
        ["TS-CD-009"],
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
    "test_distribution_list_create_with_missing_doc_returns_404": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-DL-004"],
    ),
    "test_distribution_lists_require_session_identity": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-DL-005"],
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
    "test_documents_revisions_update_rejects_rev_code_change": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-019"],
    ),
    "test_documents_create_defaults_initial_revision_code_to_start": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-022"],
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
    "test_documents_revisions_create_rejects_when_current_revision_is_final": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-025"],
    ),
    "test_documents_revisions_supersede": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-026"],
    ),
    "test_documents_revisions_supersede_rejects_final_source": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-027"],
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
    "test_documents_revisions_status_graph_rejects_ambiguous_predecessor": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-017"],
    ),
    "test_documents_revisions_status_transition_already_start": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-018"],
    ),
    "test_documents_revisions_require_session_identity": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-016"],
    ),
    "test_documents_revisions_overview_transition_from_final": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-020"],
    ),
    "test_documents_revisions_overview_transition_from_non_start_code": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-023"],
    ),
    "test_documents_revisions_overview_transition_rejects_non_final_source": (
        "documentation/test_scenarios/documents_revisions_api_test_scenarios.md",
        ["TS-REV-021"],
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
    "test_files_commented_insert_nonexistent_file": (
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
    "test_files_commented_replace": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-012"],
    ),
    "test_files_commented_replace_forbidden_for_non_owner": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-013"],
    ),
    "test_files_commented_replace_nonexistent": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-014"],
    ),
    "test_files_commented_require_session_identity": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-015"],
    ),
    "test_files_commented_delete_forbidden_for_non_owner": (
        "documentation/test_scenarios/files_commented_api_test_scenarios.md",
        ["TS-FC-016"],
    ),
    "test_written_comments_crud": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-001"],
    ),
    "test_written_comments_validation": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-002"],
    ),
    "test_written_comments_missing_revision": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-003"],
    ),
    "test_written_comments_create_rejects_user_id_field": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-004"],
    ),
    "test_written_comments_delete_forbidden_non_author": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-005"],
    ),
    "test_written_comments_update": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-006"],
    ),
    "test_written_comments_update_forbidden_non_author": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-007"],
    ),
    "test_written_comments_require_session_identity": (
        "documentation/test_scenarios/written_comments_api_test_scenarios.md",
        ["TS-WC-008"],
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
    "test_files_require_session_identity": (
        "documentation/test_scenarios/files_api_test_scenarios.md",
        ["TS-F-010"],
    ),
    "test_all_get_endpoints": (
        "documentation/test_scenarios/get_endpoints_api_test_scenarios.md",
        ["TS-GET-001"],
    ),
    "test_revision_overview_represents_single_lifecycle_path": (
        "documentation/test_scenarios/get_endpoints_api_test_scenarios.md",
        ["TS-GET-002"],
    ),
    "test_revision_overview_constraints_reject_invalid_lifecycle_updates": (
        "documentation/test_scenarios/get_endpoints_api_test_scenarios.md",
        ["TS-GET-003"],
    ),
    "test_revision_overview_transactional_reconfiguration_and_insert_guards": (
        "documentation/test_scenarios/get_endpoints_api_test_scenarios.md",
        ["TS-GET-004"],
    ),
    "test_critical_list_endpoints_match_response_models": (
        "documentation/test_scenarios/endpoint_contract_api_test_scenarios.md",
        ["TS-CTR-001"],
    ),
    "test_current_user_detail_matches_response_model": (
        "documentation/test_scenarios/endpoint_contract_api_test_scenarios.md",
        ["TS-CTR-002"],
    ),
    "test_current_user_trusted_header_takes_precedence_over_x_user_id": (
        "documentation/test_scenarios/endpoint_contract_api_test_scenarios.md",
        ["TS-CTR-003"],
    ),
    "test_current_user_invalid_trusted_header_fails_closed_even_with_valid_x_user_id": (
        "documentation/test_scenarios/endpoint_contract_api_test_scenarios.md",
        ["TS-CTR-004"],
    ),
    "test_current_user_valid_bearer_jwt_resolves_identity": (
        "documentation/test_scenarios/endpoint_contract_api_test_scenarios.md",
        ["TS-CTR-005"],
    ),
    "test_current_user_invalid_bearer_jwt_fails_closed_even_with_trusted_header": (
        "documentation/test_scenarios/endpoint_contract_api_test_scenarios.md",
        ["TS-CTR-006"],
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
    "test_notifications_create_rejects_sender_user_id_field": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-NTF-005"],
    ),
    "test_notifications_create_requires_at_least_one_recipient_target": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-NTF-006"],
    ),
    "test_notifications_require_session_identity": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-NTF-007"],
    ),
    "test_notifications_list_ignores_recipient_override_and_uses_current_user": (
        "documentation/test_scenarios/notifications_api_test_plan.md",
        ["TS-NTF-008"],
    ),
    "test_revision_code_seed_bootstrap_is_repeatable_and_preserves_identity": (
        "documentation/test_scenarios/revision_code_seed_contract_api_test_scenarios.md",
        ["TS-RCS-001"],
    ),
}

TEST_FILES = [
    "tests/api/api/test_authorization_read_rls.py",
    "tests/api/api/test_audit_fields.py",
    "tests/api/api/test_cancel_delete_endpoints.py",
    "tests/api/api/test_distribution_lists_endpoints.py",
    "tests/api/api/test_documents_revisions_endpoints.py",
    "tests/api/api/test_files_commented_endpoints.py",
    "tests/api/api/test_files_endpoints.py",
    "tests/api/api/test_endpoint_contracts.py",
    "tests/api/api/test_get_endpoints.py",
    "tests/api/api/test_notifications_endpoints.py",
    "tests/api/api/test_revision_code_seed_contract.py",
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
