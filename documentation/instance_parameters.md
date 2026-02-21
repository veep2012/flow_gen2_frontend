# Instance parameters

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-21
- Last Updated: 2026-02-21
- Version: v0.2

## Change Log
- 2026-02-21 | v0.2 | Initial dedicated registry plus documented `dl_for_each_doc` behavior with `DL_<doc_name_unique>` distribution-list naming

## Purpose
Define the source of truth for runtime configuration values stored in `ref.instance_parameters`, including expected value formats, consumers, and fallback behavior.

## Scope
- In scope:
  - Table schema and access path (`ref.instance_parameters`, `workflow.instance_parameters`).
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
  - View `workflow.instance_parameters` exposes the same data for workflow consumers.
- Resolution model:
  - Consumers query by exact parameter key.
  - Missing, invalid, or unusable values must trigger safe fallback behavior in the consumer.
- Type model:
  - Values are stored as `VARCHAR(255)` and interpreted by consumer logic.
  - Boolean-like parameters should be normalized case-insensitively in consumers (for example, `lower(trim(value))='true'`).

## Data Model
- Tables/entities:
  - `ref.instance_parameters`: parameter registry table.
  - `workflow.instance_parameters`: read-only view over `ref.instance_parameters`.
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
  - Behavior: used to build default object filename for uploaded base files.
  - Fallback: keep uploaded filename unchanged if template/user context/parts are invalid.
- `file_name_com_conv`
  - Value type: filename template string.
  - Current seed value: `<BODY>_commented_<UACR>_<TIMEST>.<EXT>`.
  - Consumer: `api/utils/helpers.py` via `_build_default_filename_from_instance_parameter(...)`, used by `POST /api/v1/files/commented/`.
  - Behavior: used to build default commented-file object name.
  - Fallback: keep original/computed source filename unchanged if template/user context/parts are invalid.
- `dl_for_each_doc`
  - Value type: boolean-like string (`true` enables behavior).
  - Current seed value: `true`.
  - Consumer: `workflow.create_document` in `ci/init/07_workflow.sql`.
  - Behavior: when true, document creation auto-creates a doc-linked distribution list with `distribution_list_name = 'DL_' || doc_name_unique`.
  - Fallback: treated as disabled when missing/unset/non-`true`.

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
- `documentation/api_interfaces.md`
- `documentation/notifications_and_dls.md`
