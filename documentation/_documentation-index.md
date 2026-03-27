# Documentation Index

## Purpose
- Provide a single entry point for all files in `documentation/`.
- Reduce navigation chaos by grouping files by purpose.
- Track ownership/status quickly using each document's `Document Control` section.

## Core Architecture
- `application_authorization_policy.md` - Authoritative business-level authorization rules for core resources and actor categories.
- `api_db_rules.md` - Backend/database contract for workflow invariants.
- `api_interfaces.md` - Current API surface and endpoint behavior.
- `auth_architecture.md` - Authentication and authorization architecture.
- `authentication_rls_matrix_as_is.md` - Current implemented authentication/authorization and RLS-related baseline (as-is snapshot).
- `authorization_rls_matrix.md` - Future-state role-based authorization and RLS matrix.
- `document_flow.md` - Document and revision lifecycle model.
- `er_diagram.md` - Entity relationship map.
- `instance_parameters.md` - Runtime parameter registry for `ref.instance_parameters` and consumer behavior.

## Process and Workflow
- `development_workflow.md` - Branching, setup, and development process.

## Feature and Domain Docs
- `current_user_photo_story.md` - Draft story for `GET /api/v1/people/users/current_user/photo` and unified MinIO-backed download handling.
- `notifications_and_dls.md` - Unified Notifications + Distribution Lists module (active source of truth).
- `distribution_list_feature.md` - Deprecated pointer; merged into `notifications_and_dls.md`.
- `distribution_list_implementation.md` - Deprecated pointer; merged into `notifications_and_dls.md`.
- `user_data_available.md` - User/person/role data availability summary.

## Test Scenarios
- `test_scenarios/audit_fields_api_test_scenarios.md` - Scenario contract for audit-field API smoke tests.
- `test_scenarios/auth_router_matrix_api_test_scenarios.md` - Router-level fail-closed auth regression matrix for changed auth-sensitive routes.
- `test_scenarios/authorization_read_rls_api_test_scenarios.md` - Scenario contract for Phase 1 read authorization/RLS coverage.
- `test_scenarios/cancel_delete_api_test_scenarios.md` - Scenario contract for revision cancel and document delete tests.
- `test_scenarios/documents_revisions_api_test_scenarios.md` - Scenario contract for revisions list/create/update/status transitions.
- `test_scenarios/endpoint_contract_api_test_scenarios.md` - Response-shape contract checks for critical list and detail endpoints.
- `test_scenarios/files_api_test_scenarios.md` - Scenario contract for file upload/update/download/validation tests.
- `test_scenarios/files_commented_api_test_scenarios.md` - Scenario contract for commented-file endpoints.
- `test_scenarios/written_comments_api_test_scenarios.md` - Scenario contract for written-comments endpoints.
- `test_scenarios/get_endpoints_api_test_scenarios.md` - Scenario contract for global GET endpoint smoke validation.
- `test_scenarios/notifications_api_test_plan.md` - End-to-end curl plan for notification lifecycle API validation.
- `test_scenarios/current_user_api_test_scenarios.md` - Contract scenarios for `GET /people/users/current_user`.
- `test_scenarios/compose_auth_smoke_test_scenarios.md` - Shell-based compose auth and ingress smoke scenarios for `make test-compose`.
- `test_scenarios/jwt_auth_validation_api_test_scenarios.md` - Fail-closed JWT/JWKS validation matrix and automated test coverage mapping.
- `test_scenarios/read_sql_guard_api_test_scenarios.md` - Static guard contract for API SQL reads using `workflow.v_*` views only.
- `test_scenarios/revision_code_seed_contract_api_test_scenarios.md` - Bootstrap and seed identity-preservation contract for revision codes and downstream references.

## Standards and Templates
- `_documentation_standards.md` - Required structure and writing rules.
- `_documentation_template.md` - Base template for new documents.
- `_naming_convention.md` - Filename rules.
- `_documentation-index.md` - This index file.
- `_documentation_actualization_state.md` - State file for monthly documentation actualization cadence.
- `story_template.md` - Lightweight template for initiative parent stories and numbered sub-stories.

## Maintenance Rules
- Add every new `documentation/*.md` file to this index in the same change.
- Keep entries lowercase to match naming convention.
- Keep helper/control files prefixed with `_`.
- Use `-` bullets for all index entries.
