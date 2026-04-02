# Repository Split Phase 3 Repository Migration And Build Enablement

## Document Control

- Status: Draft
- Owner: Product / Engineering
- Reviewers: Tech lead, frontend lead, backend lead, DevOps lead
- Created: 2026-04-02
- Last Updated: 2026-04-02
- Version: v0.1
- Related Tickets: [https://github.com/veep2012/flow_docs/issues/71](https://github.com/veep2012/flow_docs/issues/71)

## Change Log

- 2026-04-02 | v0.1 | Initial draft exact technical instruction for phase 3 repository migration and build enablement.

## Purpose

Define the exact technical instruction for phase 3 of the repository split so the team can move the current combined codebase into the new `frontend`, `backend`, and `common` repositories, clean ownership boundaries, and make each repository build and publish independently.

## Scope

- In scope:
  - copying or moving code from the combined repository into `frontend`, `backend`, and `common`
  - removing out-of-scope files from each target repository
  - fixing build logic, scripts, configuration, and documentation after the split
  - preserving backend ownership of shared product contracts
  - proving that each repository can build and publish its own artifact independently
- Out of scope:
  - the later developer cutoff
  - final production rollout
  - long-term CI optimization after bootstrap
  - application feature changes unrelated to the split

## Audience

- Frontend engineers
- Backend engineers
- Platform / DevOps engineers
- Architecture reviewers

## Definitions

- Repository migration: the act of copying or moving code and operational assets from the combined repository into the target split repositories.
- Ownership review: a structured check that confirms a repository contains only assets that belong to it.
- Build enablement: the work required to make a repository build and publish its own artifact without depending on combined-repo assumptions.
- Product contract source: the owned location of shared API and runtime integration definitions used by frontend and backend.

## Background / Context

Phase 1 created the governance baseline. Phase 2 defined the registry and artifact model. Phase 3 is the first phase that makes the split operational. It converts the new repositories from empty governance shells into independently buildable codebases. This phase must be executed carefully because copied repositories can appear separated while still retaining monorepo assumptions, hidden cross-component scripts, and unclear contract ownership.

## Requirements

### Functional Requirements

- FR-1: Frontend code and frontend build logic must be moved into the `frontend` repository.
- FR-2: Backend code and backend build logic must be moved into the `backend` repository.
- FR-3: Shared CI and tooling assets must be moved into the `common` repository only if they are truly shared and not product logic.
- FR-4: Each repository must remove files that do not belong to its ownership boundary.
- FR-5: Each repository must have a working build path that does not depend on the combined repository layout.
- FR-6: Each repository must have a publish path for its own artifact or image:
  - `frontend` -> `frontend`
  - `backend` -> `backend`
  - `common` -> `ci`
- FR-7: Shared product contracts must remain sourced from `backend`.
- FR-8: `common` must not receive business logic, API handlers, shared domain code, or frontend runtime code.
- FR-9: Scripts, documentation, and configuration copied from the combined repository must be rewritten if they still refer to monorepo-only paths or assumptions.
- FR-10: The migration must produce one recorded inventory of what was copied, what was removed, and what was rewritten in each repository.

### Non-Functional Requirements

- NFR-1: The migration must minimize accidental carry-over of hidden monorepo dependencies.
- NFR-2: The resulting repositories must be understandable without requiring engineers to inspect the old combined repository.
- NFR-3: Build and publication behavior must remain reproducible after code redistribution.
- NFR-4: The migration should prefer deterministic cleanup over ad hoc manual exceptions.
- NFR-5: The resulting repositories must align with the registry model defined in phase 2.

## Design / Behavior

### Target migration result

After phase 3:
- `frontend` contains only frontend-owned code, docs, configs, and build assets
- `backend` contains only backend-owned code, docs, configs, build assets, and shared product contract sources
- `common` contains only shared tooling, CI helpers, shared wrappers, and reusable engineering assets
- all three repositories can build independently
- all three repositories can publish their own image or artifact independently

### Technical steps

Execute phase 3 in the following order:

1. Create the migration inventory from the combined repository.
   - create one written inventory with columns:
     - asset path
     - asset type
     - target repository
     - action
     - owner
   - use only these actions:
     - `copy`
     - `move`
     - `remove`
     - `rewrite`
   - classify every top-level application, build, documentation, tooling, and configuration area from the combined repository into one of the three target repositories or mark it for removal
   - expected output: one approved migration inventory that later cleanup work must follow

2. Initialize `frontend`, `backend`, and `common` from the agreed baseline.
   - if the team uses copy-based initialization, copy the current combined repository into `frontend` and `backend`
   - for `common`, copy only the selected shared tooling/bootstrap assets rather than leaving a full repository clone in place
   - record the baseline commit or snapshot used for initialization
   - expected output: three initialized repositories with a known starting point

3. Prune the `frontend` repository to frontend ownership only.
   - remove backend application source directories
   - remove backend-only build scripts
   - remove backend-only deployment manifests
   - remove backend-only documentation
   - remove shared tooling assets that will live in `common`
   - keep only the frontend application, frontend build path, frontend docs, and only the minimum integration configuration needed to consume backend-owned contracts
   - expected output: a `frontend` repository with no backend runtime code or backend build path

4. Prune the `backend` repository to backend ownership only.
   - remove frontend application source directories
   - remove frontend-only build scripts
   - remove frontend-only deployment manifests
   - remove frontend-only documentation
   - remove shared tooling assets that will live in `common`
   - keep backend API and service code, backend build path, backend docs, and backend-owned shared product contracts
   - expected output: a `backend` repository with no frontend runtime code or frontend build path

5. Reduce the `common` repository to tooling-only content.
   - move in only shared CI helpers, reusable wrappers, common Dockerfiles, engineering templates, and shared documentation helpers
   - remove every copied application directory, domain module, API handler, and runtime feature asset
   - reject any asset whose release ownership would belong to frontend or backend rather than to shared tooling
   - expected output: a `common` repository that can be explained as tooling-only with no business logic exceptions

6. Preserve backend-owned shared product contracts.
   - identify all shared API and runtime product contract sources in the combined repository
   - move or keep those sources only in `backend`
   - replace any copied contract source in `frontend` or `common` with consumption references, generated outputs, or remove it entirely
   - record the final backend contract source locations
   - expected output: one clear backend-only source of truth for shared product contracts

7. Rewrite repository-local build and path assumptions.
   - inspect build scripts, `Makefile` targets, Dockerfiles, compose files, CI configs, and docs in each repository
   - remove combined-repo-relative paths that point outside the current repository
   - replace combined-repo assumptions with repository-local paths or documented image-based integration references
   - ensure `frontend` builds without requiring local backend source
   - ensure `backend` builds without requiring local frontend source
   - ensure `common` builds or packages shared tooling without application-source assumptions
   - expected output: repository-local build paths with no required dependency on the old combined directory structure

8. Rewrite publication configuration to the phase-2 registry model.
   - map `frontend` publication to the canonical `frontend` image path
   - map `backend` publication to the canonical `backend` image path
   - map `common` publication to the canonical `ci` image path
   - remove any old publish logic that assumes one combined repository builds multiple images in one place
   - expected output: one publication path per repository, aligned with phase 2 naming

9. Rewrite copied documentation and operational instructions.
   - remove or update any document that still describes the combined repository as the active build boundary inside the new repos
   - update repository `README.md` files so they explain:
     - repository purpose
     - how to build locally
     - what artifact is published
     - what dependencies are external to the repo
   - remove stale references to moved or deleted paths
   - expected output: each target repository explains itself without requiring combined-repo context

10. Run ownership review for each repository.
   - review `frontend` for leftover backend code, backend docs, backend-only configs, and shared tooling that belongs in `common`
   - review `backend` for leftover frontend code, frontend docs, frontend-only configs, and shared tooling that belongs in `common`
   - review `common` for any product logic, runtime modules, or contract source of truth that should not be there
   - record every rejected leftover asset and remove or relocate it before acceptance
   - expected output: signed-off ownership review for `frontend`, `backend`, and `common`

11. Run independent build verification.
   - build `frontend` from the `frontend` repository only
   - build `backend` from the `backend` repository only
   - build or package shared tooling from the `common` repository only
   - verify no build requires source code from another product repository
   - expected output: three successful independent builds

12. Run independent publication verification.
   - publish one sample `frontend` artifact or image from `frontend`
   - publish one sample `backend` artifact or image from `backend`
   - publish one sample `ci` artifact or image from `common`
   - verify each publish lands in the canonical phase-2 image path and uses the required tag/provenance model
   - expected output: three successful independent publications

13. Produce the migration record.
   - create one phase record per repository summarizing:
     - copied areas
     - removed areas
     - rewritten areas
     - remaining known cleanup items
   - any intentionally deferred non-blocking cleanup must be captured as technical debt
   - expected output: one auditable migration record for later rehearsal and cutoff planning

### Repository-specific migration rules

`frontend` must keep:
- UI source code
- frontend build and package logic
- frontend documentation
- integration configuration that consumes backend-published contracts or backend images

`frontend` must remove:
- backend runtime code
- backend contract source definitions
- backend deployment-only assets
- shared tooling that belongs in `common`

`backend` must keep:
- API and service source code
- backend build and package logic
- backend documentation
- shared product contract source definitions

`backend` must remove:
- frontend runtime code
- frontend build-only assets
- frontend deployment-only assets
- shared tooling that belongs in `common`

`common` must keep only:
- shared CI helpers
- reusable wrappers and scripts
- shared Dockerfiles for tooling
- engineering templates and documentation helpers

`common` must remove:
- frontend code
- backend code
- shared business logic
- contract source definitions
- release-owned feature modules

## Edge Cases

- A file appears in both frontend and backend because it was copied into both repos: keep a single source of truth and remove the duplicate unless it is an intentionally generated artifact.
- A build script in `frontend` still points to a backend path from the combined repository: rewrite it or fail the build-enablement review.
- A shared contract definition is accidentally copied into `frontend`: remove it and keep only the backend-owned source or generated consumer artifact.
- `common` receives a convenience utility that contains product logic: reject it from `common` and relocate it to the owning product repository.
- A repository builds only when checked out next to the old combined repository: fail phase 3 until the hidden path dependency is removed.

## Testing Strategy

- Migration verification:
  - confirm every top-level combined-repo asset is classified in the migration inventory
  - confirm each copied or moved asset has a target repository or removal decision
- Ownership verification:
  - confirm `frontend` contains no backend runtime code
  - confirm `backend` contains no frontend runtime code
  - confirm `common` contains no product logic or contract source of truth
- Build verification:
  - confirm `frontend` builds independently
  - confirm `backend` builds independently
  - confirm `common` packages or builds shared tooling independently
- Publication verification:
  - confirm `frontend` publishes to `frontend`
  - confirm `backend` publishes to `backend`
  - confirm `common` publishes to `ci`
- Contract verification:
  - confirm shared product contract sources exist only in `backend`

## Rollout / Migration

- Execute phase 3 only after phase 1 governance and phase 2 registry rules are approved.
- Complete code redistribution and cleanup before later phases depend on split-repository local development.
- Do not announce developer cutoff until independent build and publication verification are complete.
- Use the phase-3 migration record as input to rehearsal migration planning.

## Risks And Mitigations

- Risk: copied repositories keep hidden monorepo path dependencies.
  - Mitigation: run explicit build-enablement review and fail any repository that depends on combined-repo-relative paths.
- Risk: `common` becomes a dumping ground for hard-to-classify code.
  - Mitigation: require ownership review and reject any asset with product runtime ownership.
- Risk: contract ownership drifts because shared definitions are copied into multiple repositories.
  - Mitigation: keep the source of truth only in `backend` and remove copied definitions elsewhere.
- Risk: each repository builds locally but publication still assumes the old combined pipeline.
  - Mitigation: verify independent publication to canonical phase-2 image paths before phase completion.

## Open Questions

- No open questions remain in scope for this phase document.

## References

- `documentation/repo_split/repository_split_requirements_sub_story.md`
- `documentation/repo_split/repository_split_technical_vision.md`
- `documentation/repo_split/repository_split_phase_1_foundation_and_governance.md`
- `documentation/repo_split/repository_split_phase_2_registry_and_artifact_model.md`
- `documentation/_documentation_template.md`
- `documentation/_documentation_standards.md`
- `https://github.com/veep2012/flow_docs/issues/71`
