# Instance parameters

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-21
- Last Updated: 2026-03-27
- Version: v0.3

## Change Log
- 2026-03-27 | v0.3 | Synchronized parameter registry with current seed and consumer code, including exact filename-template resolution rules, `app.user`-based uploader lookup, file-upload length fallback behavior, and current `workflow.create_document` handling for `dl_for_each_doc`.
- 2026-02-21 | v0.2 | Initial dedicated registry plus documented `dl_for_each_doc` behavior with `DL_<doc_name_unique>` distribution-list naming and idempotent name-collision handling.

## Purpose
Define the source of truth for runtime configuration values stored in `ref.instance_parameters`, including expected value formats, consumers, and fallback behavior.

## Scope
- In scope:
  - Table schema and access path (`ref.instance_parameters`, `workflow.v_instance_parameters`).
  - Current parameters used by backend and workflow SQL.
  - Rules for adding new parameters.
- Out of scope:
  - Full API contracts (documented in `documentation/api_interfaces.md`).
  - UI-only feature flags that are not persisted in this table.

## Audience
- Backend engineers
- Database maintainers
- API maintainers

## Definitions
- Instance parameter: key-value runtime setting row in `ref.instance_parameters`.
- Parameter key: unique `parameter` column value.
- Consumer: API or SQL function that reads a parameter and applies behavior.

## Design / Behavior
- Storage model:
  - Table `ref.instance_parameters` stores one row per parameter key.
  - View `workflow.v_instance_parameters` exposes the same data for workflow consumers.
- Resolution model:
  - Consumers query by exact parameter key.
  - Missing, invalid, or unusable values must trigger safe fallback behavior in the consumer.
  - The current repository seeds exactly three parameters: `file_name_conv`, `file_name_com_conv`, and `dl_for_each_doc`.
- Type model:
  - Values are stored as `VARCHAR(255)` and interpreted by consumer logic.
  - Boolean-like parameters should be normalized case-insensitively in consumers (for example, `lower(trim(value))='true'`).
- File-naming consumer model:
  - `api/utils/helpers.py::_build_default_filename_from_instance_parameter(...)` reads the template from `workflow.v_instance_parameters`.
  - The helper resolves the uploader acronym by reading `workflow.v_users` for `current_setting('app.user', true)`, which is the transaction-local effective user id written by API request setup.
  - Template rendering currently supports `<DOCNO>`, `<BODY>`, `<UACR>`, `<TIMEST>`, and `<EXT>`.
  - Any failed prerequisite must fall back to the original filename rather than fail the request.

## Data Model
- Tables/entities:
  - `ref.instance_parameters`: parameter registry table.
  - `workflow.v_instance_parameters`: read-only view over `ref.instance_parameters`.
- Key fields:
  - `parameter` (`VARCHAR(64)`, PK): unique key.
  - `value` (`VARCHAR(255)`, NOT NULL): raw configured value.
  - `description` (`VARCHAR(1024)`, nullable): human-readable meaning.
- Constraints:
  - Primary key on `parameter`.
  - `value` is required.

## Parameter Registry
- `file_name_conv`
  - Value type: filename template string.
  - Current seed value: `<DOCNO>-<BODY>_<UACR>_<TIMEST>.<EXT>`.
  - Consumer: `api/utils/helpers.py` via `_build_default_filename_from_instance_parameter(...)`, used by `POST /api/v1/files/`.
  - Behavior: used to build the object-storage filename for uploaded base files after MIME validation and before MinIO object-key construction.
  - Rendering inputs:
    - `<DOCNO>` = `workflow.v_documents.doc_name_unique` for the target revision.
    - `<BODY>` = sanitized basename of the uploaded filename.
    - `<UACR>` = sanitized uppercase uploader acronym resolved from current `app.user`.
    - `<TIMEST>` = current UTC timestamp in `%Y%m%dT%H%M%SZ` format.
    - `<EXT>` = sanitized lowercase filename extension.
  - Fallback: keep uploaded filename unchanged if the uploaded basename/extension is invalid, the template is missing, the effective uploader cannot be resolved, `<DOCNO>` is required but no document name is available, the rendered filename is invalid, or the rendered filename exceeds the router-enforced 90-character maximum.
- `file_name_com_conv`
  - Value type: filename template string.
  - Current seed value: `<BODY>_commented_<UACR>_<TIMEST>.<EXT>`.
  - Consumer: `api/utils/helpers.py` via `_build_default_filename_from_instance_parameter(...)`, used by `POST /api/v1/files/commented/`.
  - Behavior: used to build the object-storage filename for commented files from the source file metadata selected by `file_id`.
  - Rendering inputs:
    - `<BODY>` = sanitized basename of the source file linked by `file_id`.
    - `<UACR>` = sanitized uppercase uploader acronym resolved from current `app.user`.
    - `<TIMEST>` = current UTC timestamp in `%Y%m%dT%H%M%SZ` format.
    - `<EXT>` = sanitized lowercase extension of the source filename.
  - Fallback: keep the source filename unchanged if template/user context/parts are invalid or the rendered output is not a usable filename.
- `dl_for_each_doc`
  - Value type: boolean-like string (`true` enables behavior).
  - Current seed value: `true`.
  - Consumer: `workflow.create_document` in `ci/init/07_workflow.sql`.
  - Behavior: after inserting the document and its initial revision, document creation auto-creates a doc-linked distribution list with `distribution_list_name = 'DL_' || doc_name_unique` and `doc_id = new doc_id`.
  - Collision handling: if a row with the same `distribution_list_name` already exists, insertion is skipped (`ON CONFLICT DO NOTHING`) and document creation continues.
  - Fallback: treated as disabled when missing, null, empty, or any trimmed/lowercased value other than `true`.

## Requirements
### Functional Requirements
- FR-1: Every new parameter must include a stable key, value, and clear description in seed/migration scripts.
- FR-2: Every parameter consumer must define explicit fallback behavior for missing or invalid values.
- FR-3: Any new parameter must be documented in this file in the same change as code/SQL usage.

### Non-Functional Requirements
- NFR-1: Parameter parsing must be deterministic and case normalization rules must be explicit in consumer logic.
- NFR-2: Fallback behavior must avoid breaking API/DB flows when parameter lookup fails.

## Edge Cases
- Missing parameter row: consumer must apply safe default behavior.
- Empty/whitespace value: consumer should treat as invalid unless explicitly supported.
- Invalid template tokens: consumer must fall back without raising unhandled errors.
- Overlong rendered filename: filename consumer must fall back to original filename.
- `<DOCNO>` present in a filename template but no document name available: filename consumer must fall back to the original filename.
- Effective uploader identity missing from `app.user`: filename consumer must fall back to the original filename.

## Rollout / Migration
- Backward compatibility:
  - New parameters are additive and should not break existing consumers.
- Data migration steps:
  - Add parameter rows via migration/seed scripts.
  - Update this registry and linked API/domain docs in the same PR.
- Deployment notes:
  - Ensure environments receive seed/migration updates before enabling dependent code paths.

## References
- `ci/init/02_ref.sql`
- `ci/init/08_views.sql`
- `ci/init/flow_seed.sql`
- `ci/init/07_workflow.sql`
- `api/utils/helpers.py`
- `api/routers/files.py`
- `api/routers/files_commented.py`
- `api/routers/documents.py`
- `documentation/api_interfaces.md`
- `documentation/notifications_and_dls.md`
