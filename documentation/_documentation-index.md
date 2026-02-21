# Documentation Index

## Purpose
- Provide a single entry point for all files in `documentation/`.
- Reduce navigation chaos by grouping files by purpose.
- Track ownership/status quickly using each document's `Document Control` section.

## Core Architecture
- `api_db_rules.md` - Backend/database contract for workflow invariants.
- `api_interfaces.md` - Current API surface and endpoint behavior.
- `auth_architecture.md` - Authentication and authorization architecture.
- `authorization_rls_matrix.md` - Future-state role-based authorization and RLS matrix.
- `document_flow.md` - Document and revision lifecycle model.
- `er_diagram.md` - Entity relationship map.
- `instance_parameters.md` - Runtime parameter registry for `ref.instance_parameters` and consumer behavior.

## Process and Workflow
- `development_workflow.md` - Branching, setup, and development process.

## Feature and Domain Docs
- `notifications_and_dls.md` - Unified Notifications + Distribution Lists module (active source of truth).
- `distribution_list_feature.md` - Deprecated pointer; merged into `notifications_and_dls.md`.
- `distribution_list_implementation.md` - Deprecated pointer; merged into `notifications_and_dls.md`.
- `user_data_available.md` - User/person/role data availability summary.

## Test Scenarios
- `test_scenarios/audit_fields_api_test_scenarios.md` - Scenario contract for audit-field API smoke tests.
- `test_scenarios/cancel_delete_api_test_scenarios.md` - Scenario contract for revision cancel and document delete tests.
- `test_scenarios/documents_revisions_api_test_scenarios.md` - Scenario contract for revisions list/create/update/status transitions.
- `test_scenarios/files_api_test_scenarios.md` - Scenario contract for file upload/update/download/validation tests.
- `test_scenarios/files_commented_api_test_scenarios.md` - Scenario contract for commented-file endpoints.
- `test_scenarios/written_comments_api_test_scenarios.md` - Scenario contract for written-comments endpoints.
- `test_scenarios/get_endpoints_api_test_scenarios.md` - Scenario contract for global GET endpoint smoke validation.
- `test_scenarios/notifications_api_test_plan.md` - End-to-end curl plan for notification lifecycle API validation.

## Standards and Templates
- `_documentation_standards.md` - Required structure and writing rules.
- `_documentation_template.md` - Base template for new documents.
- `_naming_convention.md` - Filename rules.
- `_documentation-index.md` - This index file.
- `_documentation_actualization_state.md` - State file for monthly documentation actualization cadence.

## Maintenance Rules
- Add every new `documentation/*.md` file to this index in the same change.
- Keep entries lowercase to match naming convention.
- Keep helper/control files prefixed with `_`.
- Use `-` bullets for all index entries.
