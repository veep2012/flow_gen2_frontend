# Application Authorization Policy

## Document Control
- Status: Review
- Owner: Product, Backend, and Database Team
- Reviewers: Security and API maintainers
- Created: 2026-03-18
- Last Updated: 2026-03-18
- Version: v1.0

## Change Log
- 2026-03-18 | v1.0 | Established the first authoritative application-level authorization policy for core Flow resources, actor categories, on-behalf rules, and implementation mapping expectations.

## Purpose
Define the business-level authorization policy for Flow so endpoint reviews, workflow SQL, and tests can validate behavior against one source of truth.

## Scope
- In scope:
  - Business authorization rules for core resources:
    - `doc`
    - `doc_revision`
    - `files`
    - `files_commented`
    - `written_comments`
    - `notifications`
    - `distribution_list`
  - Actor categories and allowed actions.
  - On-behalf-of and cross-user access policy.
  - Mapping expectations from business policy to API, DB workflow, and tests.
- Out of scope:
  - Authentication transport details.
  - Low-level RLS policy syntax.
  - UI presentation and navigation rules.

## Policy Status
This document is normative for business authorization decisions.

If current implementation, API docs, workflow SQL, or tests differ from this policy, they must be treated as drift and brought back into alignment.

## Actor Model

### Authenticated actor
A request with a valid effective internal user identity resolved by the API and DB session context.

### Unauthenticated actor
A request without a valid effective identity. Unauthenticated actors may not read or mutate protected business resources.

### Scoped contributor
An authenticated actor whose assigned role and scope allow access to the target document lineage or related business object.

### Resource owner
An authenticated actor who created the specific resource or is recorded on it as the responsible user for actor-sensitive ownership decisions.

Examples:
- written comment author
- commented-file owner
- notification sender
- notification recipient for inbox/read state

### Superuser
An authenticated actor with explicit superuser authority. Superuser may bypass ordinary ownership and scope restrictions where stated below, but must still act through authenticated, auditable paths.

## Global Rules

### GR-1 Identity required
All protected business actions require an authenticated actor. Anonymous access must fail closed.

### GR-2 Least privilege
An actor may perform only the minimum actions allowed by their role, scope, and ownership relationship to the target resource.

### GR-3 Scope before write
For document-lineage resources, write actions require the actor to be authorized for the underlying business object, not just to reach the endpoint.

### GR-4 Ownership-sensitive actions
Certain actions are intentionally narrower than ordinary scoped write access and require resource ownership or superuser authority.

### GR-5 No implicit cross-user action
A caller may not act on behalf of another user merely by supplying another user's id in request payloads, query params, or headers.

### GR-6 Explicit on-behalf policy
On-behalf-of behavior is forbidden by default. It is allowed only when all of the following are true:
- the endpoint contract explicitly supports it
- the actor is privileged to do it
- the action is auditable as delegated behavior
- tests and documentation explicitly cover it

### GR-7 Current-user semantics
Endpoints representing "my inbox", "my read state", "my authored content", or equivalent user-bound views must derive the acting user from effective session identity, not from caller-supplied target-user fields.

### GR-8 Fail closed on ambiguity
If scope, ownership, lineage, or actor identity cannot be resolved confidently, the action must be denied.

## Resource Policy Matrix

### Documents (`doc`)
| Action | Allowed actor | Notes |
| --- | --- | --- |
| Create | Scoped contributor with write authority for target project/area/unit, or superuser | Caller may not create on behalf of another owner unless explicitly defined by product policy and audited. |
| Read/list | Scoped contributor with read authority, or superuser | Read visibility is scope-based, not ownership-based. |
| Update metadata | Scoped contributor with write authority, or superuser | Applies to ordinary editable document fields. |
| Delete/void | Scoped contributor with write authority when workflow permits, or superuser | Must remain subject to workflow/business-state rules. |

### Revisions (`doc_revision`)
| Action | Allowed actor | Notes |
| --- | --- | --- |
| Create | Scoped contributor with write authority on parent document, or superuser | Revision authorship is derived from effective actor. |
| Read/list | Scoped contributor with read authority on parent document, or superuser | Scope follows parent document lineage. |
| Update editable fields | Scoped contributor with write authority when revision status permits, or superuser | Business-state gates still apply. |
| Transition status | Scoped contributor with write authority when workflow permits, or superuser | Not ownership-only. Controlled by workflow rules plus auth. |
| Cancel | Scoped contributor with write authority when workflow permits, or superuser | Same as status mutation: scoped write + workflow legality. |

### Files (`files`)
| Action | Allowed actor | Notes |
| --- | --- | --- |
| Create/upload | Scoped contributor with write authority on parent revision/document, or superuser | Must also satisfy status/business rules. |
| Read/list/download | Scoped contributor with read authority on parent lineage, or superuser | Scope follows revision/document lineage. |
| Update/replace metadata or blob | Scoped contributor with write authority on parent lineage, or superuser | Must also satisfy workflow/status restrictions. |
| Delete if supported | Scoped contributor with write authority when workflow permits, or superuser | No caller-supplied actor override. |

### Commented Files (`files_commented`)
| Action | Allowed actor | Notes |
| --- | --- | --- |
| Create | Scoped contributor with write authority on parent lineage, or superuser | Ownership is set from effective actor. |
| Read/list/download | Scoped contributor with read authority on parent lineage, or superuser | Scope follows underlying file/revision/document lineage. |
| Replace | Commented-file owner or superuser | This is stricter than generic scoped write. |
| Delete | Commented-file owner or superuser | This is stricter than generic scoped write. |

### Written Comments (`written_comments`)
| Action | Allowed actor | Notes |
| --- | --- | --- |
| Create | Scoped contributor with write authority on parent revision, or superuser | Author is always derived from effective actor. |
| Read/list | Scoped contributor with read authority on parent lineage, or superuser | Scope follows revision/document lineage. |
| Update | Comment author or superuser | Ownership-sensitive action. |
| Delete | Comment author or superuser | Ownership-sensitive action. |

### Notifications (`notifications`)
| Action | Allowed actor | Notes |
| --- | --- | --- |
| Create/send | Scoped contributor allowed to notify within the referenced business context, or superuser | Sender is always derived from effective actor. |
| List inbox | Current recipient only, or a separate privileged endpoint if ever added | Default endpoint is current-user inbox only. |
| Mark read | Current recipient only | Read state is recipient-specific and may not be set for another user. |
| Replace | Original sender or superuser | Ownership-sensitive action. |
| Drop/delete | Original sender or superuser | Ownership-sensitive action. |

### Distribution Lists (`distribution_list`)
| Action | Allowed actor | Notes |
| --- | --- | --- |
| Create | Scoped contributor with write authority for the relevant document context, or superuser | Global and doc-linked list creation both require authenticated authority. |
| Read/list | Scoped contributor with read authority for the relevant context, or superuser | Visibility should not exceed related document/business scope. |
| Add/remove members | Scoped contributor with write authority for the relevant context, or superuser | Membership administration is not a public action. |
| Delete | Scoped contributor with write authority when business rules permit, or superuser | Still blocked when list is in active use according to workflow/business rules. |

## On-Behalf and Cross-User Policy

### Forbidden by default
The following are forbidden unless a dedicated privileged contract is added later:
- create a resource while specifying another user as the acting author/sender/owner
- mark another user's notification as read
- list another user's notification inbox through the default inbox endpoint
- update or delete another user's ownership-sensitive resource based only on scoped access

### If delegated administration is added later
Any future delegated or cross-user action must include:
- a separate explicit API contract
- a documented privileged actor category
- audited delegated actor and target actor identity
- dedicated negative and positive tests
- corresponding workflow and API documentation updates

## Business-to-Implementation Mapping

### API contract expectations
- Actor-sensitive fields such as sender, author, owner, or inbox recipient must be derived from effective session identity unless this document explicitly allows otherwise.
- Caller-supplied cross-user overrides must be rejected or ignored on default user-bound endpoints.
- Endpoint docs must state whether an action is:
  - scope-based
  - owner-only
  - sender-only
  - recipient-only
  - superuser-only
  - mixed owner-or-superuser / scoped-or-superuser

### Database workflow expectations
- Workflow SQL must enforce business authorization consistently with this policy before performing state changes.
- Scope-derived checks belong in shared authorization predicates and workflow prechecks.
- Ownership-sensitive checks must remain explicit in workflow functions where the business rule is narrower than generic scoped write access.

### Test expectations
- Every ownership-sensitive or cross-user-sensitive rule in this document should have automated negative coverage.
- Scenario docs must map critical policy rules to smoke/integration tests.
- When product policy changes, the policy document, endpoint docs, workflow logic, and tests must be updated in the same change.

## Current Explicit Policy Decisions
- Notification inbox listing is current-user only on the default endpoint.
- Notification read state is current-recipient only.
- Notification replace/drop is sender-or-superuser only.
- Written comment update/delete is author-or-superuser only.
- Commented-file replace/delete is owner-or-superuser only.
- Document-lineage reads are scope-based, not owner-based.

## Known Follow-Up Gaps
- Final product rules for status-gated file and commented-file writes still need a dedicated allowed-status matrix.
- Distribution-list visibility and administration should be validated against final business scope rules as doc-linked/global usage evolves.
- If delegated administration becomes a product requirement, it must be designed explicitly rather than inferred from existing actor fields.

## References
- `documentation/authentication_rls_matrix_as_is.md`
- `documentation/authorization_rls_matrix.md`
- `documentation/api_db_rules.md`
- `documentation/api_interfaces.md`
- `documentation/notifications_and_dls.md`
- `tech-debt/2026-03-13.md`
