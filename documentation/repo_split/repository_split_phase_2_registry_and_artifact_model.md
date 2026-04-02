# Repository Split Phase 2 Registry And Artifact Model

## Document Control

- Status: Draft
- Owner: Product / Engineering
- Reviewers: Tech lead, frontend lead, backend lead, DevOps lead
- Created: 2026-04-02
- Last Updated: 2026-04-02
- Version: v0.1
- Related Tickets: [https://github.com/veep2012/flow_docs/issues/70](https://github.com/veep2012/flow_docs/issues/70)

## Change Log

- 2026-04-02 | v0.1 | Initial draft exact technical instruction for repository split phase 2 registry and artifact model.

## Purpose

Define the exact technical instruction for phase 2 of the repository split so the team can stand up the registry model, standardize image naming and provenance, and make artifact consumption predictable across development, validation, and production.

## Scope

- In scope:
  - defining the internal container registry layout for team-built images
  - defining the approved external registry sources for infrastructure images
  - defining image naming, tagging, provenance, and promotion rules
  - defining version pinning rules for validation and production
  - defining local fallback behavior when the internal remote registry is unavailable
- Out of scope:
  - application code migration between repositories
  - full CI/CD implementation details
  - production deployment orchestration details beyond image sourcing rules
  - the later developer cutoff

## Audience

- Frontend engineers
- Backend engineers
- Platform / DevOps engineers
- Architecture reviewers

## Definitions

- Internal container registry: the team-controlled registry that publishes team-built images.
- External container registry: an approved third-party or platform registry that provides infrastructure images not built by the team.
- Image provenance: the traceable origin of a container image, including which registry and repository produced it.
- Pinned image: an image referenced by immutable version or digest rather than by a floating tag alone.
- Local fallback: a documented local registry or preloaded image path used when the internal remote registry is temporarily unavailable.

## Background / Context

Phase 2 exists to prevent image-source ambiguity before repository migration depends on registries. The split delivery model assumes that frontend, backend, and shared tooling can publish independent images, while production also consumes infrastructure images from an approved external source. Without one written artifact model, developers and pipelines will mix floating tags, undocumented sources, and ad hoc fallbacks.

## Requirements

### Functional Requirements

- FR-1: The internal container registry must publish team-built images for `frontend`, `backend`, and `ci`.
- FR-2: The approved external container registry sources must cover `postgres`, `keycloak`, `oauth2-proxy`, and `nginx`.
- FR-3: Each internal image must have one canonical repository name and one documented ownership source.
- FR-4: The artifact model must define which environments may use floating `latest` tags and which must use pinned versions.
- FR-5: Validation and production must use pinned image versions or digests.
- FR-6: The artifact model must define how image provenance is recorded for internal and external images.
- FR-7: The artifact model must define how images are promoted from build output to validated release candidates and production-approved references.
- FR-8: The artifact model must define a documented local fallback for internal images when the remote internal registry is unavailable.
- FR-9: The artifact model must define how frontend, backend, and shared tooling images are consumed by local development environments.
- FR-10: The artifact model must distinguish team-built application images from externally sourced infrastructure images.

### Non-Functional Requirements

- NFR-1: Image naming must be simple enough that developers and automation use the same references without translation layers.
- NFR-2: Provenance must remain auditable across development, validation, and production.
- NFR-3: The model must reduce accidental use of floating tags in controlled environments.
- NFR-4: Local fallback must be explicit and operational rather than informal tribal knowledge.
- NFR-5: The artifact model must support independent publication of frontend, backend, and shared tooling images.

## Design / Behavior

### Internal registry layout

The internal registry must publish the following canonical image repositories:

- `frontend`
- `backend`
- `ci`

Expected ownership:

- `frontend`: published from the `frontend` repository and owned by the frontend delivery flow
- `backend`: published from the `backend` repository and owned by the backend delivery flow
- `ci`: published from the `common` repository and owned by the shared tooling delivery flow

### External registry layout

The approved external registry must provide the following infrastructure images:

- `postgres`
- `keycloak`
- `oauth2-proxy`
- `nginx`

These images are approved consumption sources only. They are not owned or rebuilt by the product repositories unless a separate decision later changes that model.

### Technical steps

Execute phase 2 in the following order:

1. Create the internal registry inventory record.
   - create one written table with columns:
     - image name
     - internal registry path
     - owning repository
     - publishing automation identity
     - allowed environments
   - add exactly these rows:
     - `frontend`
     - `backend`
     - `ci`
   - expected output: one approved inventory record that later pipeline and deployment work must reuse without renaming paths

2. Create the internal registry repositories or namespaces.
   - create or confirm the exact internal paths for `frontend`, `backend`, and `ci`
   - confirm each path can store tagged images and expose immutable digests
   - confirm deletion and overwrite policy for published images
   - expected output:
     - three reachable internal image paths
     - one documented registry base URL
     - one documented retention or immutability policy

3. Create publication credentials and write boundaries.
   - create one publication credential or service identity for `frontend`
   - create one publication credential or service identity for `backend`
   - create one publication credential or service identity for `ci`
   - grant each identity write access only to its own image path and read access to the others only if operationally required
   - expected output: a credential-to-image-path matrix with least-privilege access

4. Create the external image allowlist record.
   - create one written table with columns:
     - runtime service
     - external registry source
     - approved pinned version or digest
     - approval owner
     - review cadence
   - add exactly these rows:
     - `postgres`
     - `keycloak`
     - `oauth2-proxy`
     - `nginx`
   - expected output: one approved external image allowlist for controlled environments

5. Freeze canonical naming.
   - record the final internal image names exactly as:
     - `frontend`
     - `backend`
     - `ci`
   - forbid aliases or alternate image names in later docs, scripts, or pipelines
   - bind each image name to its owning future repository:
     - `frontend` -> `frontend`
     - `backend` -> `backend`
     - `ci` -> `common`
   - expected output: one canonical naming rule that later phases must not reinterpret

6. Define the mandatory tag contract for internal images.
   - for every internal image push, require:
     - optional `latest`
     - one pinned release or semantic version if available
     - one immutable build identifier
     - captured digest
   - define the build identifier format once and reuse it consistently
   - expected output: one tag-format rule that every image publication job must follow

7. Define the environment consumption matrix.
   - create one written matrix with rows:
     - local development
     - issue reproduction
     - rehearsal migration
     - validation or CI compatibility
     - pre-production
     - production
   - for each row, state whether `latest` is allowed
   - required rule:
     - only local development may use `latest`
     - all other environments must use pinned references
   - expected output: one environment-to-reference policy with no ambiguity

8. Define provenance storage.
   - choose one authoritative provenance location for internal images
   - choose one authoritative provenance location for external approvals
   - minimum internal fields:
     - source repository
     - source commit
     - build identifier
     - image path
     - pushed tags
     - digest
     - publication timestamp
   - minimum external fields:
     - runtime service
     - external registry source
     - approved version or digest
     - approval owner
     - approval timestamp
   - expected output: one auditable provenance record shape that later automation can fill

9. Define promotion control.
   - create one promotion table with stages:
     - build output
     - validation candidate
     - production-approved reference
   - for each stage, record:
     - who can assign the stage
     - what evidence is required
     - which environments may consume that stage
   - required rule:
     - no image may be promoted if provenance is missing
     - no different binary may reuse an already approved pinned version
   - expected output: one promotion-control rule for internal and approved external references

10. Implement the fallback package for internal images.
   - choose exactly one primary fallback mechanism:
     - local registry mirror
     - preloaded archive
     - pre-seeded approved local images
   - define the operational steps to load:
     - `frontend`
     - `backend`
     - `ci`
   - define:
     - who declares outage mode
     - where fallback artifacts are stored
     - how fallback image versions are identified
     - how teams return to normal remote-registry mode
   - expected output: one executable fallback runbook

11. Publish sample images and verify the model.
   - push one sample `frontend` image with the full required tag set
   - push one sample `backend` image with the full required tag set
   - push one sample `ci` image with the full required tag set
   - capture provenance for all three samples
   - capture approved pinned references for `postgres`, `keycloak`, `oauth2-proxy`, and `nginx`
   - expected output: one validated example set proving the naming, pinning, and provenance rules work in practice

12. Run the failure-path verification.
   - simulate internal remote registry unavailability
   - load the three internal sample images through the documented fallback path
   - verify the loaded images still expose visible pinned identifiers
   - record any missing operational step or metadata gap
   - expected output: signed-off fallback rehearsal result that later phases can depend on

### Image naming and tagging rules

Use the following baseline naming and tagging model for internal images:

- canonical repositories:
  - `frontend`
  - `backend`
  - `ci`
- convenience floating tags allowed:
  - `latest`
- required pinned tags:
  - semantic version or release version where available
  - immutable build identifier
  - digest for production approval where the platform supports it

Required rules:

- every pushed internal image must have at least one pinned identifier in addition to any optional `latest` tag
- `latest` may be used only for convenience in developer-oriented workflows
- validation, rehearsal migration, pre-production, and production must not depend on `latest` alone
- external infrastructure images must also be referenced by approved pinned version or digest in controlled environments

### Image provenance rules

For every internal image, record:

- source repository
- source commit or build identifier
- published image reference
- publication timestamp

For every approved external image, record:

- external registry source
- approved version or digest
- approval owner
- approval date

The provenance record may be implemented through release metadata, pipeline logs, deployment metadata, or another auditable mechanism, but it must be reproducible and reviewable.

### Promotion model

Promotion must follow these stages:

- build output:
  - image is built and published with pinned identifier
- validation candidate:
  - image is selected for integration, CI compatibility, or rehearsal migration
- production-approved reference:
  - image version or digest is explicitly approved for production use

Promotion rules:

- do not retag a different binary to an already approved pinned version
- do not promote images with unknown provenance
- do not promote external floating tags without captured version or digest

### Environment usage rules

Development environments:

- may use `latest` for convenience when developers are explicitly testing current integration behavior
- should prefer pinned versions when reproducing a specific issue
- must be able to pull:
  - `frontend`
  - `backend`
  - `ci`

Validation environments:

- must use pinned internal images
- must use approved pinned external infrastructure images

Production environments:

- must use pinned internal images
- must use approved pinned external infrastructure images
- must keep the internal registry and external registry sources explicit in deployment records

### Local fallback model

When the internal remote registry is unavailable, the team must support one documented fallback path for internal images.

Allowed fallback mechanisms:

- local registry mirror
- preloaded local image archive
- pre-seeded developer workstation images for approved pinned versions

Fallback rules:

- fallback is for internal images only unless a separate platform rule exists for external images
- fallback usage must still preserve image identity and version visibility
- fallback must support at minimum:
  - `frontend`
  - `backend`
  - `ci`
- fallback instructions must be executable by developers and CI operators without ad hoc undocumented steps

### Deliverables of phase 2

Phase 2 is complete only when the following artifacts exist:

- documented internal registry image list for `frontend`, `backend`, and `ci`
- documented external registry image list for `postgres`, `keycloak`, `oauth2-proxy`, and `nginx`
- written naming and tagging rules for internal images
- written rule that validation and production use pinned versions
- written provenance recording rule for internal and external images
- documented promotion stages from build to validation to production-approved reference
- documented local fallback procedure for internal images

## Edge Cases

- A developer uses `latest` in pre-production by mistake: the deployment must be rejected or corrected to a pinned reference before approval.
- The internal registry is unavailable during integration work: the documented local fallback must provide usable `frontend`, `backend`, and `ci` images.
- An external image publisher updates a floating tag unexpectedly: controlled environments must continue using the approved pinned version or digest.
- `frontend` and `backend` images are built from incompatible commits: compatibility validation must fail on the pinned image pair rather than silently retagging one side.
- A fallback image is present locally but its source version is unclear: it must not be treated as an approved validation or production candidate.

## Testing Strategy

- Manual verification:
  - confirm the internal registry has canonical repositories for `frontend`, `backend`, and `ci`
  - confirm the approved external image list exists for `postgres`, `keycloak`, `oauth2-proxy`, and `nginx`
  - confirm internal images are published with pinned identifiers and not only `latest`
  - confirm validation and production documentation forbid floating-only references
  - confirm the fallback procedure can resolve `frontend`, `backend`, and `ci`
- Artifact verification:
  - publish one sample internal image for each canonical repository
  - verify provenance metadata is captured for each published image
  - verify one approved external image can be referenced by pinned version or digest
- Failure-path verification:
  - simulate internal remote registry unavailability and verify the documented local fallback path works

## Rollout / Migration

- Establish the registry model before repository migration depends on image publication.
- Create the internal image repositories before enabling cross-repository local integration.
- Document the external image allowlist before building the first fully containerized production-like deployment.
- Apply pinning rules before rehearsal migration and before any pre-production deployment.
- Test the local fallback path before later migration phases assume the remote registry is always available.

## Risks and Mitigations

- Risk: developers and automation rely on `latest` and lose reproducibility.
  - Mitigation: require pinned references for validation and production and document `latest` as convenience-only.
- Risk: external infrastructure images drift unexpectedly.
  - Mitigation: approve and record pinned external versions or digests.
- Risk: registry outage blocks local or CI workflows.
  - Mitigation: provide one documented local fallback path for internal images.
- Risk: provenance becomes unclear across internal and external sources.
  - Mitigation: require explicit provenance records for every approved image source.
- Risk: image naming diverges between documents and pipelines.
  - Mitigation: define one canonical repository name per image and use it consistently everywhere.

## Open Questions

- No open questions remain in scope for this phase document.

## References

- `documentation/repo_split/repository_split_requirements_sub_story.md`
- `documentation/repo_split/repository_split_technical_vision.md`
- `documentation/repo_split/repository_split_phase_1_foundation_and_governance.md`
- `documentation/_documentation_template.md`
- `documentation/_documentation_standards.md`
- `https://github.com/veep2012/flow_docs/issues/70`
