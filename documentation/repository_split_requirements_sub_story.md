# 0. Define Repository Split Requirements

## Document Control

- Status: Draft
- Owner: Product / Engineering
- Reviewers: Tech lead, frontend lead, backend lead, DevOps lead
- Created: 2026-04-01
- Last Updated: 2026-04-01
- Version: v0.1
- Related Tickets: TBD

## Change Log

- 2026-04-01 | v0.1 | Initial draft sub-story defining requirements and target operating model for future frontend/backend repository separation.

## Purpose

Define the sub-story and the decision-driving requirements for separating frontend and backend into independent repositories so future implementation choices stay aligned with one agreed operating model.

## Scope

- In scope:
  - ownership boundaries between frontend and backend after repository separation
  - access expectations for engineers, CI/CD, and release automation
  - local developer workflow expectations for working across two repositories
  - artifact distribution expectations for frontend deliverables and backend deployables
  - integration expectations between frontend and backend after the split
  - non-functional constraints that must guide the split design
- Out of scope:
  - selecting the final Git hosting topology or organization structure
  - executing the repository split
  - detailed CI/CD pipeline implementation
  - production infrastructure redesign beyond what is required to support the split

## Audience

- Product owners
- Frontend engineers
- Backend engineers
- Platform / DevOps engineers
- Architecture reviewers

## Definitions

- Repository split: the future state in which frontend and backend source code are maintained in separate version-controlled repositories.
- Ownership boundary: the explicit limit of responsibility for code, build logic, documentation, and release artifacts for a given team.
- Integration contract: the agreed interface that allows independently delivered frontend and backend components to work together.
- Artifact distribution: the method used to publish, version, and consume build outputs between repositories and deployment environments.

## Background / Context

The current codebase is maintained as a combined implementation. In that model, UI and API developers can easily affect each other's areas in the same repository. In practice, this creates avoidable conflicts: a UI-focused change can also modify backend code, including changes made through low-control or "vibe coding" workflows that bypass the approved backend architecture and contract expectations. The risk increases when frontend and backend contributors have different levels of seniority, because changes in a neighboring component may be merged without enough domain ownership and can cause architectural drift or regressions.

The team now needs a shared requirement baseline before deciding how to separate frontend and backend into independent repositories. Without a written target operating model, implementation decisions can drift across tooling, ownership, access, delivery, and integration concerns. This sub-story is intended to establish that baseline and keep later design and execution work consistent.

## Description

As a team, we want a clear set of requirements for separating frontend and backend into independent repositories so that implementation decisions can be made consistently and follow an agreed target operating model.

This sub-story covers the future-state requirements that must be satisfied before the repository split is implemented. It should produce a single reviewable requirements baseline that downstream architecture, migration, and delivery work can use without re-deciding the same operating assumptions.

## Requirements

### Functional Requirements

- FR-1: The future-state operating model must define which assets belong to the frontend repository and which assets belong to the backend repository.
- FR-2: The requirements must define ownership boundaries for application code, shared contracts, build and release configuration, and developer-facing documentation after separation.
- FR-3: The requirements must define how shared contracts between frontend and backend are created, versioned, reviewed, and consumed after the split, including one explicit source of truth for each contract, with backend ownership as the default for shared product contracts unless an exception is explicitly approved.
- FR-4: The requirements must define the minimum access levels expected for frontend engineers, backend engineers, platform engineers, and automation accounts in each repository.
- FR-5: The requirements must define how local development works when a change affects both repositories, including how developers obtain compatible versions of frontend and backend locally.
- FR-6: The requirements must define how environment configuration and secrets responsibilities are divided between the separated repositories without duplicating ownership ambiguities.
- FR-7: The requirements must define what build artifacts each repository produces and where those artifacts are published or made available for downstream use.
- FR-8: The requirements must define how frontend deliverables locate and communicate with backend services across local, test, and production-like environments after separation.
- FR-9: The requirements must define the expected integration points that remain between repositories, including API contracts, configuration inputs, and release compatibility expectations.
- FR-10: The requirements must define the decision points that later implementation stories must preserve, even if tooling choices change.
- FR-11: The requirements must define whether common cross-repository tooling is owned in a separate shared repository and, if so, which assets are allowed there.
- FR-12: If a shared tooling repository is used, the requirements must define how common scripts, `make` helpers, engineering standards, and reusable automation are versioned, published, and consumed by frontend and backend repositories.
- FR-13: If Docker is used as the delivery mechanism for shared tooling, the requirements must define which common tasks run through versioned Docker images and how product repositories invoke them locally and in CI.
- FR-14: Generated SDK or client packages, if used, must be treated as delivery artifacts derived from backend-owned contracts unless a separate ownership exception is explicitly approved.
- FR-15: Shared environment variable contracts between repositories must be limited to a minimal approved intersection only.
- FR-16: CI interfaces and shared `make` targets that are moved into a common repository must have explicit ownership in that common repository and be versioned as shared operational tooling contracts.
- FR-17: If shared tooling is distributed through container registries, the operating model must support fallback to a local registry or preloaded local images when the remote container registry is unavailable.
- FR-18: The operating model must define which development environments run application code directly from repositories and which dependent images they pull from registries for integration support.
- FR-19: The operating model must define which production containers are pulled from the team's internal container registry and which supporting infrastructure containers are pulled from an approved external container registry.
- FR-20: The operating model must define the production HTTP entrypoint, including that the compiled frontend application is served through a containerized runtime on port `80`.

### Non-Functional Requirements

- NFR-1: The operating model should allow frontend and backend repositories to be developed, validated, and released independently unless a documented integration dependency requires coordination.
- NFR-2: The requirements must reduce ownership ambiguity by making repository responsibility boundaries explicit and reviewable.
- NFR-3: The target model should keep local developer setup practical for engineers who need to run both components together during feature work or debugging.
- NFR-4: The target model must support traceable artifact provenance so teams can identify which repository version produced a deployed asset.
- NFR-5: The target model should support secure least-privilege access for people and automation across both repositories.
- NFR-6: The target model should minimize coupling between repository internals and rely on stable published contracts or artifacts instead of cross-repository source assumptions.
- NFR-7: The requirements should be implementation-agnostic enough to survive specific tooling changes, while remaining concrete enough to guide architecture and migration work.
- NFR-8: Any shared repository should stay narrowly scoped so it does not become an unmanaged home for business logic, feature code, or ambiguous cross-team ownership.
- NFR-9: If shared tooling is delivered through Docker images, the approach should keep local workflows understandable, versioned, and efficient enough for daily use.
- NFR-10: Shared environment and tooling contracts should be minimized so cross-repository coupling stays intentional and reviewable.
- NFR-11: Shared tooling distribution should remain operational during temporary remote container registry outages through a documented local fallback path.
- NFR-12: Production container provenance should remain explicit so teams can distinguish internally built images from externally sourced infrastructure images.

## Design / Behavior

The target operating model should treat the frontend and backend as independently owned delivery units with explicit integration contracts.

Expected requirement themes:

- Ownership boundaries:
  - frontend repository owns frontend application code, frontend build configuration, frontend deployment packaging, and frontend-focused documentation
  - backend repository owns backend service code, backend build configuration, backend deployment packaging, and backend-focused documentation
  - shared frontend/backend product contracts should be backend-owned by default as the primary source of truth, unless a specific contract is explicitly assigned to a different owner
  - REST API schemas, auth and permission response behavior, and backend-produced event schemas are backend-owned with no planned exceptions in this story
  - shared frontend/backend product contracts should remain in one clearly owned source of truth, rather than becoming an unowned byproduct of a neutral repository
  - any shared contract material must have a defined system of record and a defined consumption path
  - a separate shared repository may be used for common tooling, engineering standards, and reusable delivery helpers, but not as a default home for product behavior
- Access expectations:
  - repository permissions should be aligned to team responsibility and least privilege
  - CI/CD identities should have only the repository and artifact permissions required for their delivery path
  - cross-repository write access should be exceptional and explicitly justified
- Local developer workflow:
  - developers must be able to clone, start, and validate each repository independently
  - developers who work across the boundary should have a documented way to run compatible frontend and backend versions together
  - local integration should prefer published contracts, versioned packages, or documented compatibility rules over ad hoc manual coordination
  - repository-specific application run and debug workflows should stay local to each repository for speed and clarity
  - frontend development environments should run UI code directly from the frontend repository while pulling backend and CI-support images when needed for integration
  - backend development environments should run API code directly from the backend repository while pulling frontend and CI-support images when needed for integration
- Artifact distribution:
  - each repository should publish versioned outputs that downstream environments or pipelines can consume without direct source coupling
  - frontend distribution requirements should define how static assets or frontend bundles are versioned and promoted
  - backend distribution requirements should define how deployable service artifacts are versioned and promoted
  - generated SDK or client packages, if adopted, should be published as delivery artifacts derived from backend-owned contracts rather than treated as separately owned product contracts
  - shared tooling, if separated into a common repository, should be published as versioned reusable artifacts rather than consumed through direct source-copying
  - Docker images are an acceptable delivery mechanism for shared tooling when they provide stable execution environments for common validation, code generation, documentation checks, and reusable CI tasks across repositories
  - if shared tooling images are normally pulled from a remote container registry, the operating model should also support a documented local registry or preloaded-image fallback for outage scenarios
  - the team's internal container registry should publish at least frontend, backend, and CI/tooling images or their approved versioned equivalents
  - approved external infrastructure images such as PostgreSQL, Keycloak, NGINX, and OAuth2 Proxy may be sourced from a separate external container registry when they are not team-built images
- Integration expectations:
  - backend API behavior exposed to the frontend must remain available through a documented contract
  - shared environment configuration between frontend and backend should stay intentionally minimal and be limited to approved integration keys only
  - compatibility expectations between frontend and backend releases must be explicit
  - integration validation should confirm that independently built artifacts work together in local integration workflow, CI validation, and at least one shared pre-production environment before production promotion
  - production should run as a fully containerized environment with explicit image sources for application and infrastructure services

Recommended ownership model:

- backend-owned product contracts should remain the default source of truth for frontend/backend integration behavior
- no explicit non-backend ownership exceptions are approved in this sub-story for shared frontend/backend product contracts
- any future exception to backend ownership should name the alternative owner and the reason for that exception
- a separate common repository is reasonable for shared `make` helpers, CI support, engineering templates, documentation standards, and similar cross-repository tooling
- if the common repository uses Docker, product repositories should consume versioned images through thin local wrappers instead of embedding duplicated heavy scripting
- the common repository should start with one shared tooling image while the shared task set remains small, and split into smaller task-focused images only when image size or task complexity justifies it
- cross-repository automation should allow artifact publication and compatibility validation, but should not require one product repository to change or release as part of the other repository's normal delivery path

Suggested downstream split of work after this sub-story:

- `1. Define target architecture and contract ownership`
- `2. Define repository access and automation model`
- `3. Define local development and integration workflow`
- `4. Plan migration and rollout`

## Edge Cases

- A change touches both repositories and a shared contract at the same time: the operating model must define how compatibility is preserved and reviewed across both delivery streams.
- One repository must release while the other stays unchanged: the target model should allow this when the published contract is unchanged.
- Frontend and backend release cadences diverge: the target model must define compatibility expectations so teams do not require lockstep releases by default.
- A developer needs to debug an integration issue locally across both repositories: the local workflow must remain feasible without undocumented setup steps.
- A shared artifact or contract publication fails: the operating model should make the failure visible and prevent silent drift between repositories.
- A common tooling Docker image changes in a way that breaks one consuming repository: the operating model must require explicit versioning and controlled upgrades instead of implicit latest-tag coupling.

## Acceptance Criteria

- A numbered sub-story exists for defining repository split requirements and follows the repository story template structure.
- The sub-story states clear functional requirements covering ownership boundaries, access expectations, local developer workflows, artifact distribution, and integration expectations after separation.
- The sub-story states clear non-functional requirements that constrain independence, security, traceability, coupling, and developer usability.
- The sub-story is broad enough to guide later design and migration work without prescribing one mandatory tooling implementation.
- The document is indexed in `documentation/_documentation-index.md`.

## Definition of Done

- Story and documentation content are completed.
- Relevant documentation is updated.
- Relevant review is completed.
- Open questions affecting delivery are resolved or explicitly recorded.

## Risks and Mitigations

- Risk: the requirements remain too vague and later stories re-open basic operating-model decisions.
  - Mitigation: keep the requirements explicit around boundaries, access, workflow, artifacts, and integration expectations.
- Risk: the requirements become too tool-specific and constrain future implementation options unnecessarily.
  - Mitigation: define mandatory outcomes and guardrails separately from optional implementation choices.
- Risk: ownership of shared contracts remains unclear after the split.
  - Mitigation: require one defined system of record and one defined publication/consumption path for every shared contract.
- Risk: a common repository grows into a dumping ground for unrelated shared code or hidden business logic.
  - Mitigation: explicitly limit the common repository to shared tooling, standards, and automation assets with named ownership.
- Risk: Docker-based shared tooling slows down or obscures local developer workflows.
  - Mitigation: require thin repository-local wrappers, explicit image versioning, and selective use of containers only for genuinely shared tasks.

## Open Questions

- No open questions remain in scope for this sub-story. Future exceptions to backend-owned product contract ownership require explicit review and documented justification in a follow-up story or architecture decision.

## References

- `documentation/story_template.md`
- `documentation/_documentation_template.md`
- `documentation/_documentation_standards.md`
- `documentation/_documentation-index.md`
- `documentation/repository_split_technical_vision.md`
