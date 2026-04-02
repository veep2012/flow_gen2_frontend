# Repository Split Phase 1 Foundation And Governance

## Document Control
- Status: Draft
- Owner: Product / Engineering
- Reviewers: Tech lead, frontend lead, backend lead, DevOps lead
- Created: 2026-04-02
- Last Updated: 2026-04-02
- Version: v0.1
- Related Tickets: https://github.com/veep2012/flow_docs/issues/69

## Change Log
- 2026-04-02 | v0.1 | Initial draft exact technical instruction for repository split phase 1 foundation and governance.

## Purpose
Define the exact technical instruction for phase 1 of the repository split so the team can create the target repositories, apply governance controls, and lock the ownership model before code migration starts.

## Scope
- In scope:
  - creating the `frontend`, `backend`, and `common` repositories
  - defining the baseline ownership and allowed content for each repository
  - configuring branch protection, CODEOWNERS, and automation access
  - defining the old combined repository state before and after the later developer cutoff
- Out of scope:
  - migrating source code into the new repositories
  - implementing CI/CD pipelines beyond minimum bootstrap governance
  - executing the later developer cutoff
  - production deployment changes

## Audience
- Frontend engineers
- Backend engineers
- Platform / DevOps engineers
- Architecture reviewers

## Definitions
- Combined repository: the current single repository that still hosts frontend and backend before the split is completed.
- Developer cutoff: the later migration milestone after which normal commits to the combined repository stop and all normal development moves to the split repositories.
- Common repository: the repository that owns shared CI, tooling, templates, and engineering automation only.
- Automation identity: a CI/CD or service account that needs controlled repository or registry access.

## Background / Context
Phase 1 exists to remove governance ambiguity before code is copied or moved. The repository split will fail if teams create new repositories without clear ownership, protection rules, or access boundaries. This phase does not move application code. It prepares the control plane so later migration work can happen against stable repository contracts.

## Requirements
### Functional Requirements
- FR-1: Three repositories must be created for `frontend`, `backend`, and `common`.
- FR-2: Each repository must have one explicit ownership purpose and one explicit list of allowed assets.
- FR-3: Shared product contracts must remain backend-owned by default.
- FR-4: The `common` repository must be explicitly limited to shared tooling, templates, standards, and reusable CI assets.
- FR-5: Each repository must have branch protection on the default branch before normal team use begins.
- FR-6: Each repository must include a `CODEOWNERS` file before code migration starts.
- FR-7: Human access and automation access must be defined separately and follow least privilege.
- FR-8: The combined repository must remain active during phase 1 and may become read-only only in the later cutoff phase.

### Non-Functional Requirements
- NFR-1: Governance must be applied before repository migration so ownership drift does not begin on day one.
- NFR-2: Access rules must be simple enough for teams to understand without per-user exceptions as the default model.
- NFR-3: The repository model must minimize the chance of cross-component edits outside the owning team.
- NFR-4: The baseline setup must be reproducible across environments and auditable by engineering leadership.

## Design / Behavior
### Target repositories
- `frontend` repository:
  - owns UI source code
  - owns frontend build and packaging logic
  - owns frontend-focused documentation
  - must not own backend application logic
- `backend` repository:
  - owns API and service source code
  - owns backend build and packaging logic
  - owns backend-focused documentation
  - owns shared product contracts by default
- `common` repository:
  - owns shared CI helpers, tooling wrappers, engineering templates, and documentation standards
  - may publish the shared `ci` image or equivalent shared tooling artifacts
  - must not own product features, API logic, or frontend runtime code

### Required repository bootstrap
Create the three repositories with the following baseline:
- default branch: `main`
- repository visibility: match the current combined repository visibility unless security review requires stricter access
- initial files:
  - `README.md`
  - `.gitignore`
  - `CODEOWNERS`
  - repository description matching its ownership purpose
- issue and pull request settings enabled
- branch deletion disabled for protected `main`

### Required ownership statements
Add a short ownership statement to each repository `README.md` at creation time:
- `frontend`: `Owns ui code and frontend build/publication only.`
- `backend`: `Owns api code, backend build/publication, and shared product contracts by default.`
- `common`: `Owns shared ci/tooling assets only. No business logic.`

### Branch protection baseline
Apply the following minimum protection to `main` in all three repositories:
- require pull request before merge
- require at least 1 approval
- dismiss stale approvals on new commits
- block force pushes
- block branch deletion
- require status checks before merge once CI exists
- restrict direct pushes to administrators and approved automation only

Phase 1 may bootstrap the repositories before all status checks exist. In that case:
- enable pull-request-only merge protection immediately
- add required status checks as soon as each repository pipeline becomes available

### CODEOWNERS baseline
Create `CODEOWNERS` in each repository using role-based team ownership. Replace the example team slugs with the actual organization team names during execution.

`frontend`:
```text
* @org/frontend-leads @org/platform-leads
```

`backend`:
```text
* @org/backend-leads @org/platform-leads
```

`common`:
```text
* @org/platform-leads
```

If the organization requires secondary reviewers, add them after the owning lead team rather than replacing the owning team.

### Access model
Use the following baseline access matrix:

| Role | Frontend | Backend | Common |
| --- | --- | --- | --- |
| Frontend engineers | Write | Read | Read |
| Backend engineers | Read | Write | Read |
| Platform / DevOps engineers | Admin or Maintain | Admin or Maintain | Admin or Maintain |
| Architecture / tech leads | Maintain | Maintain | Maintain |
| CI/CD automation for frontend | Write only where needed for checks/releases | Read | Read |
| CI/CD automation for backend | Read | Write only where needed for checks/releases | Read |
| CI/CD automation for common | Read | Read | Write only where needed for checks/releases |

Access rules:
- do not grant default cross-repository human write access between frontend and backend teams
- use team-based access, not named-user grants, unless there is a documented exception
- automation identities must be separated by responsibility instead of one shared admin bot
- registry credentials must be scoped to the image paths each automation identity actually publishes

### Allowed content in `common`
`common` may contain:
- shared `make` fragments
- CI templates and reusable pipeline scripts
- engineering standards and documentation helpers
- shared Dockerfiles for CI or reusable validation tooling
- wrapper scripts used by both product repositories

`common` must not contain:
- frontend runtime source code
- backend runtime source code
- shared domain logic
- API handlers or API contract source of truth
- code that requires feature-level release ownership

### Combined repository state
The combined repository remains the active development source during phase 1.

Required state rules:
- do not set the combined repository to read-only in phase 1
- do not remove existing write permissions in phase 1 unless they are unrelated cleanup
- document that the combined repository becomes read-only only after the later developer cutoff is approved and executed
- prepare the read-only archive procedure now so the later cutoff is operationally simple

### Deliverables of phase 1
Phase 1 is complete only when the following artifacts exist:
- three created repositories
- repository descriptions aligned to ownership purpose
- `README.md` ownership statement in each repository
- branch protection on `main` in each repository
- `CODEOWNERS` in each repository
- approved team-based access model for humans and automation
- written rule that `common` is tooling-only
- written rule that shared product contracts are backend-owned by default

## Edge Cases
- A platform engineer asks to place a shared service library in `common`: reject it unless it is pure tooling and not product logic.
- Frontend needs temporary write access to `backend` during migration setup: grant only time-bound exception access with documented owner approval.
- CI is not yet available when repositories are created: apply pull-request-only protection first, then add required checks when pipelines exist.
- One automation account needs to publish multiple image paths: split credentials by publication responsibility where the platform allows it; otherwise document the exception explicitly.
- Teams disagree whether a shared file belongs in `backend` or `common`: default to `backend` if the file affects product behavior or product contracts.

## Testing Strategy
- Manual verification:
  - confirm the three repositories exist
  - confirm `main` is protected in each repository
  - confirm direct push is blocked for normal contributors
  - confirm each repository contains a `CODEOWNERS` file
  - confirm team permissions match the approved access matrix
  - confirm `common` contains only bootstrap tooling content
- Governance verification:
  - simulate a pull request in each repository and confirm approval rules are enforced
  - simulate a direct push attempt by a non-admin contributor and confirm it is rejected
  - confirm automation identities cannot write to repositories or registries outside their scope

## Rollout / Migration
- Create the repositories before any code extraction work starts.
- Apply branch protection and CODEOWNERS before inviting normal team usage.
- Approve team and automation access before first bootstrap commits.
- Keep the combined repository as the active source until later migration phases validate the split workflow.
- Do not announce developer cutoff as part of phase 1. Phase 1 only prepares the governance baseline required for that later step.

## Risks and Mitigations
- Risk: `common` becomes a hidden fourth application repository.
  - Mitigation: publish and enforce an allowed-content list and reject business logic there.
- Risk: teams receive broad cross-write access for convenience and the ownership boundary collapses immediately.
  - Mitigation: use team-based least-privilege access and document exceptions explicitly.
- Risk: repositories are created without branch protection and bootstrap commits bypass review.
  - Mitigation: make protection setup part of repository creation, not a later cleanup task.
- Risk: the combined repository is frozen too early and migration work stalls.
  - Mitigation: keep it active until the later cutoff phase and document that rule here.

## Open Questions
- Which actual organization team slugs will replace the role-based `@org/...` placeholders in `CODEOWNERS` and access control?
- Should repository visibility remain identical to the current combined repository, or does security review require a stricter default for one or more target repositories?

## References
- `documentation/repo_split/repository_split_requirements_sub_story.md`
- `documentation/repo_split/repository_split_technical_vision.md`
- `documentation/_documentation_template.md`
- `documentation/_documentation_standards.md`
- `https://github.com/veep2012/flow_docs/issues/69`
