# Frontend Repository Phase 3 Prune Record

## Document Control

- Status: Draft
- Owner: Frontend engineering
- Reviewers: Frontend lead, backend lead, DevOps lead
- Created: 2026-04-02
- Last Updated: 2026-04-02
- Version: v0.1
- Related Tickets: [https://github.com/veep2012/flow_docs/issues/71](https://github.com/veep2012/flow_docs/issues/71)

## Change Log

- 2026-04-02 | v0.1 | Recorded the frontend repository prune, removed backend-owned assets, and documented the remaining frontend-only build and integration boundary.

## Purpose

Record the frontend-specific migration outcome for phase 3 so the repository split has an auditable summary of what was removed, what was rewritten, and which integration assumptions remain in the frontend repository.

## Scope

- In scope:
  - frontend repository cleanup performed in phase 3
  - removed backend code, tests, manifests, and tooling
  - rewritten frontend-local build, test, and image entrypoints
  - remaining backend integration configuration consumed by the frontend
- Out of scope:
  - backend repository pruning details
  - common repository tooling migration details
  - later CI publication wiring outside this repository

## Audience

- Frontend engineers
- Backend engineers
- Platform / DevOps engineers
- Architecture reviewers

## Definitions

- Frontend-owned asset: source, build logic, or documentation that exists only to build, validate, or operate the frontend application.
- Backend-owned contract source: the source-of-truth definition for shared frontend/backend behavior that must remain outside this repository.
- Shared tooling asset: reusable engineering helper content that should live in the `common` repository rather than in a product repository.

## Background / Context

Phase 3 of the repository split requires each copied repository to be reduced to its ownership boundary. This repository started as a copy of the combined codebase, so it contained backend runtime code, backend tests, combined compose assets, and shared local skills. The prune removed those non-frontend areas and rewrote the remaining repo entrypoints so the frontend can build and validate without a local backend source tree.

## Requirements

### Functional Requirements

- FR-1: The frontend repository must contain no backend runtime source directories.
- FR-2: The frontend repository must contain no backend-only build scripts, deployment manifests, or backend test suites.
- FR-3: The frontend repository must keep one working frontend-local validation path and one frontend image build path.
- FR-4: The frontend repository must consume backend integration only through minimal configuration inputs instead of backend source copies.
- FR-5: The migration record must state the removed areas, rewritten areas, and remaining known cleanup items for this repository.

### Non-Functional Requirements

- NFR-1: The remaining frontend repository should be understandable without combined-repository context.
- NFR-2: Frontend validation should be reproducible from this repository alone.
- NFR-3: The prune should minimize accidental reintroduction of backend or shared-tooling ownership drift.

## Design / Behavior

Removed areas:
- backend runtime and database source under `api/`
- backend test suites under `tests/`
- backend Python and test configuration at the repository root
- backend and combined compose assets under `ci/` except the frontend image Dockerfile
- backend and shared shell or PowerShell scripts under `scripts/`
- backend-only and combined-repository documentation outside `documentation/repo_split/`
- repository-local skill and technical-debt scaffolding intended to move into `common`

Rewritten areas:
- `Makefile` now exposes frontend-only targets for local UI dev, validation, and image build
- `README.md` now describes only the frontend repository boundary and workflow
- `AGENTS.md` now blocks reintroduction of backend-owned assets
- `ci/Dockerfile.ui` now uses the frontend lockfile and deterministic `npm ci`
- `scripts/local-ui-runtime.sh` now treats formatting as a check instead of mutating files during lint

Retained frontend-owned areas:
- `ui/` application source, tests, and built assets
- `scripts/local-ui-container.sh` and `scripts/local-ui-runtime.sh`
- `ci/Dockerfile.ui`
- `documentation/repo_split/` split-planning and migration records

Remaining backend integration configuration:
- `VITE_API_BASE_URL`
- `VITE_AUTH_START_URL`

These variables are consumer-side integration inputs only. They do not make this repository the owner of backend contract source.

## Edge Cases

- A future frontend task tries to add backend OpenAPI or schema source directly into this repository: reject that change and consume the published backend contract artifact or runtime endpoint instead.
- A future local workflow requires backend source checkout to build the frontend: treat that as a phase 3 regression and rewrite the workflow.
- A future shared automation helper is proposed for this repository root: move it to `common` unless it is clearly frontend-specific.

## Testing Strategy

- Run `make test` to verify frontend unit tests, lint/format checks, and production build complete from this repository alone.
- Run `make image-build` to verify the frontend runtime image builds from frontend-owned files only.
- Inspect the remaining top-level paths to confirm no backend runtime or backend build path remains.

## Rollout / Migration

- Backward compatibility:
  - frontend runtime configuration still supports externally supplied backend URLs through `VITE_API_BASE_URL` and `VITE_AUTH_START_URL`
- Data migration steps:
  - none in this repository
- Deployment notes:
  - later CI publication wiring must publish the frontend image without reintroducing combined-repository assumptions

## Risks and Mitigations

- Risk: a later change reintroduces backend-owned helper scripts because they are convenient locally.
  - Mitigation: keep frontend-only ownership rules in `AGENTS.md` and review new top-level additions against the phase 3 boundary.
- Risk: split-planning documents drift from the actual remaining repository surface.
  - Mitigation: keep this prune record updated when repository-boundary changes occur.

## Open Questions

- Should the remaining split-planning documents stay in this repository long term, or move to a shared governance location after the split stabilizes?
- Should the frontend runtime image continue to serve `vite preview`, or switch to a dedicated static-serving runtime in a later phase?

## References

- `documentation/repo_split/repository_split_phase_3_repository_migration_and_build_enablement.md`
- `documentation/repo_split/repository_split_technical_vision.md`
- `README.md`
- `Makefile`
- `ci/Dockerfile.ui`
