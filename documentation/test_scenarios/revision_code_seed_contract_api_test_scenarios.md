# Revision Code Seed Contract API Test Scenarios

## Document Control
- Status: Review
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-03-20
- Last Updated: 2026-03-20
- Version: v0.2

## Change Log
- 2026-03-20 | v0.2 | Narrowed the contract to the current repository policy: revision-code safety is guaranteed through clean bootstrap and reseed only; in-place migration is explicitly out of scope until a future migration framework exists.

## Purpose
Define the automated verification contract for revision-code bootstrap and reseed behavior so published `rev_code_id` identities remain stable and safe for downstream references.

## Scope
- In scope:
  - clean bootstrap via `ci/init/flow_init.psql`
  - deterministic revision-code seeding via `ci/init/flow_seed.sql`
  - stable seeded `rev_code_id` identity mapping
  - foreign-key safety for `core.doc_revision.rev_code_id`
  - post-seed sequence advancement above explicit seeded IDs
- Out of scope:
  - in-place migration tooling or upgrade validation for existing deployed databases
  - endpoint-specific response payload validation

## Design / Behavior
The repository contract supports clean bootstrap and reseed only. For now, revision-code safety means a recreated database must install the canonical `revision_overview` rows with stable `rev_code_id` identities, preserve downstream references created after bootstrap, and leave the identity sequence above the seeded range.

## Scenario Catalog
- `TS-RCS-001`: revision-code bootstrap is repeatable and preserves seeded identity plus downstream foreign-key validity.

## Scenario Details

### TS-RCS-001 Repeatable Bootstrap Preserves Revision-Code Identity
- Intent: Prove that the supported clean bootstrap path preserves the documented `rev_code_id` mapping and does not orphan downstream references.
- Setup/Preconditions:
  - a disposable PostgreSQL database can be created and dropped
  - `ci/init/flow_init.psql` and `ci/init/flow_seed.sql` are available from the repository root
  - seeded prerequisite reference rows exist for `workflow.create_document` and `workflow.update_revision`
- Request/Action:
  - create an empty disposable database
  - run `ci/init/flow_init.psql`
  - run `ci/init/flow_seed.sql`
  - verify `ref.revision_overview` matches the documented fixed mapping:
    - `1 -> IDC -> next 2`
    - `2 -> IFRC -> next 3`
    - `3 -> AFD -> next 4`
    - `4 -> AFC -> next 5`
    - `5 -> AS-BUILT -> final terminal`
    - `6 -> INDESIGN -> next 1 and start`
  - verify the `rev_code_id` sequence advances above the seeded range
  - create a document revision using seeded `rev_code_id = 6`
  - update that revision to seeded `rev_code_id = 1`
  - verify no `core.doc_revision.rev_code_id` rows are left without a matching `ref.revision_overview.rev_code_id`
  - rerun `ci/init/flow_init.psql` and `ci/init/flow_seed.sql` against the same disposable database and repeat the assertions
- Expected:
  - both bootstrap passes succeed
  - the seeded `rev_code_id` mapping is identical after each pass
  - the sequence value continues above `6`
  - create and update operations using seeded `rev_code_id` values succeed
  - downstream `core.doc_revision` rows remain fully referenced
- Cleanup:
  - drop the disposable database

## Automated Test Mapping
- `tests/api/api/test_revision_code_seed_contract.py::test_revision_code_seed_bootstrap_is_repeatable_and_preserves_identity` -> `TS-RCS-001`

## References
- `tests/api/api/test_revision_code_seed_contract.py`
- `ci/init/flow_init.psql`
- `ci/init/flow_seed.sql`
- `ci/init/03_core.sql`
- `documentation/api_db_rules.md`
- `documentation/document_flow.md`
