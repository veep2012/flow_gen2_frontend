# Current User Photo Story

## Document Control
- Status: Draft
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-03-19
- Last Updated: 2026-03-19
- Version: v0.1
- Related Tickets: TBD

## Change Log
- 2026-03-19 | v0.1 | Initial draft story for `GET /api/v1/people/users/current_user/photo` and unified MinIO download handling.

## Purpose
Define the current understanding of a backlog story for serving the authenticated user's profile photo from MinIO through a new API endpoint.

## Scope
- In scope:
  - new endpoint proposal: `GET /api/v1/people/users/current_user/photo`
  - expected HTTP contract and failure behavior
  - alignment with existing `files` and `files_commented` download behavior
  - implementation direction for shared MinIO streaming logic
- Out of scope:
  - UI changes that consume the new endpoint
  - photo upload/update workflow changes
  - broader people/user CRUD redesign

## Audience
- Backend Team
- API maintainers
- UI consumers that need a stable photo-download contract

## Definitions
- Current user: authenticated user resolved from DB session identity via the same mechanism as `GET /api/v1/people/users/current_user`.
- Photo object: MinIO object addressed by `ref/person.photo_s3_uid` in the current read model.
- Unified download procedure: one shared backend flow for reading metadata, fetching MinIO objects, setting download/stream headers, and closing MinIO responses.

## Background / Context
The current API already exposes `GET /api/v1/people/users/current_user` and returns user details derived from session identity. The user-related data model already carries `photo_s3_uid`, and the backend already has working MinIO streaming patterns for:
- `GET /api/v1/files/{file_id}/download`
- `GET /api/v1/files/commented/download?id=...`

At the moment, current-user photo retrieval is not exposed as a dedicated binary endpoint. A new endpoint is needed, and the implementation should not introduce a third copy of the MinIO download flow.

## Requirements
### Functional Requirements
- FR-1: The backend must expose `GET /api/v1/people/users/current_user/photo`.
- FR-2: The endpoint must resolve the actor using the same effective identity rules as `GET /api/v1/people/users/current_user`.
- FR-3: The endpoint must read the current user's `photo_s3_uid` from the existing read model rather than bypassing the established people/user lookup path.
- FR-4: When a current user cannot be resolved, the endpoint must preserve the same auth contract as the current-user detail endpoint.
- FR-5: When the current user resolves but has no photo configured, the endpoint should return a stable not-found contract instead of a synthetic empty file.
- FR-6: The endpoint must stream the MinIO object to the client and return consistent download headers, including `Content-Disposition`, `ETag`, `Last-Modified`, and `Accept-Ranges: none`.
- FR-7: The implementation should reuse the same MinIO response lifecycle handling already used by file-download endpoints, including retry behavior and response cleanup.
- FR-8: The implementation should avoid introducing a third bespoke download code path in `api/routers/people.py`.

### Non-Functional Requirements
- NFR-1: The endpoint should reuse existing helper functions where practical so download behavior remains consistent across resources.
- NFR-2: Logging should be consistent with existing download endpoints and include enough context to troubleshoot MinIO failures without leaking secrets.
- NFR-3: The endpoint should continue to honor current MinIO retry and time-skew handling from `api/utils/minio.py`.

## Design / Behavior
Recommended API shape:
- Endpoint: `GET /api/v1/people/users/current_user/photo`
- Authentication model: same as current-user detail endpoint
- Response body on success: binary stream, not JSON
- Object source: MinIO object referenced by the resolved current user's `photo_s3_uid`

Recommended response contract:
- `200 OK`: photo stream returned successfully.
- `401 Unauthorized`: no effective session identity exists.
- `404 Not Found`: current user does not resolve, no photo is configured, or the configured object cannot be resolved in storage.
- `416 Range Not Satisfiable`: range requests are not supported, matching existing file-download behavior.
- `502 Bad Gateway`: MinIO access fails after retry handling.

Recommended implementation direction:
- Extract a shared helper for MinIO-backed downloads instead of duplicating the logic in `files`, `files_commented`, and `people`.
- The shared helper should centralize:
  - `Range` header rejection
  - MinIO `get_object` and `stat_object`
  - content-disposition header building
  - `ETag` and `Last-Modified` propagation
  - streaming response creation
  - `BackgroundTask(_close_minio_response, response)`
- Resource-specific routers should remain responsible for:
  - authorization and identity resolution
  - DB lookup of the resource-specific `s3_uid`
  - resource-specific not-found detail messages
  - the preferred filename presented to clients

Suggested DB lookup shape:
- Resolve effective current user ID exactly as `GET /api/v1/people/users/current_user` does.
- Query the existing user/person read model for `photo_s3_uid` and, if available, a preferred display filename or content type source.
- If `photo_s3_uid` is null or empty, return `404`.

Filename behavior options:
- Preferred: derive a stable filename such as `<user_acronym>_photo` plus extension when recoverable from the object key or content type.
- Acceptable initial fallback: use the MinIO object key basename.

## API Contract (If Applicable)
- Endpoint: `GET /api/v1/people/users/current_user/photo`
- Request:
```http
GET /api/v1/people/users/current_user/photo HTTP/1.1
Authorization: Bearer <token>
```
- Response:
```http
HTTP/1.1 200 OK
Content-Type: image/jpeg
Content-Disposition: attachment; filename="FDQC_photo.jpg"; filename*=UTF-8''FDQC_photo.jpg
ETag: "abc123"
Last-Modified: Wed, 19 Mar 2026 10:00:00 GMT
Accept-Ranges: none
```
- Errors:
  - `401`: no effective session identity exists
  - `404`: current user not found, photo not configured, or object not found
  - `416`: range requests are not supported
  - `502`: MinIO access failed after retry handling

## Security / Permissions (If Applicable)
- Access model:
  - authenticated current user only
- Authorization rules:
  - the endpoint should expose only the authenticated user's own photo
  - it should not accept arbitrary `user_id` or `person_id` selectors
- Audit/logging impact:
  - log start and ready events similarly to existing file downloads
  - avoid logging credentials or signed storage details

## Edge Cases
- Current user resolves but `photo_s3_uid` is null: return `404`.
- Current user resolves but the MinIO object has been deleted: return `404` or a single stable not-found contract if that is preferred for clients.
- Object metadata lacks a content type: fall back to `application/octet-stream`.
- Client sends `Range` header: return `416`.
- Stored object key basename is unsafe for headers: sanitize it the same way as existing file-download flows.

## Testing Strategy
- Unit tests:
  - current-user identity missing returns `401`
  - current-user unresolved returns `404`
  - null `photo_s3_uid` returns `404`
  - shared download helper builds consistent headers
- Integration tests:
  - photo object streams successfully from MinIO
  - MinIO missing object path returns expected contract
  - parity checks against `files` and `files_commented` download headers
- Manual verification:
  - call the endpoint with a user that has a configured photo
  - call the endpoint with a user that has no configured photo

## Rollout / Migration
- Backward compatibility:
  - additive API change only
- Data migration steps:
  - none expected if `photo_s3_uid` is already populated where needed
- Deployment notes:
  - no new MinIO configuration should be required beyond current runtime settings

## Risks and Mitigations
- Risk: a third copy-pasted download implementation drifts from `files` and `files_commented`.
  - Mitigation: extract and adopt a shared MinIO streaming helper before or during endpoint implementation.
- Risk: unclear `404` semantics for “user missing”, “photo missing”, and “object missing” create client ambiguity.
  - Mitigation: decide and document whether these states intentionally collapse into one stable `404` contract.
- Risk: filename derivation for photos is inconsistent.
  - Mitigation: define one filename policy in the shared helper contract or resource wrapper.

## Open Questions
- Should the endpoint use `inline` or `attachment` in `Content-Disposition` for browser-friendly avatar rendering?
- Should “photo not configured” and “photo object missing in MinIO” collapse into the same `404` detail?
- Do we want a shared helper in `api/utils/minio.py`, a dedicated response-builder module, or a router-local abstraction reused by all three resources?
- Should the current-user detail endpoint eventually expose a photo URL/path alongside `photo_s3_uid`?

## References
- `api/routers/people.py`
- `api/routers/files.py`
- `api/routers/files_commented.py`
- `api/utils/minio.py`
- `documentation/api_interfaces.md`
- `documentation/test_scenarios/current_user_api_test_scenarios.md`
- `documentation/user_data_available.md`
