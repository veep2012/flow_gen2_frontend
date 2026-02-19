---
name: api-rmm-guard
description: Guard API design against regressions below Richardson Maturity Model Level 2. Use when creating, updating, or reviewing HTTP endpoints, methods, status semantics, and URI design in `api/routers/`.
---

# API RMM Guard

## Overview

Use this skill to keep the API at **RMM Level 2 or higher**:
- Resource-oriented URIs
- Correct HTTP method semantics
- Meaningful HTTP status codes

This skill does not require HATEOAS; it prevents backsliding to Level 0/1 patterns.

## Workflow (Required)

### Step 1: Classify endpoint change
Choose all that apply:
- New endpoint
- Existing endpoint behavior change
- Refactor/rename path
- Review-only (no code change)

### Step 2: Evaluate against RMM checks
- **Resource URI check**:
  - Prefer nouns/resources (`/documents/{id}/revisions`)
  - Flag RPC-style action paths where avoidable (`/doThing`, `/process`, `/run`)
- **HTTP method check**:
  - `GET` read-only
  - `POST` create/non-idempotent action
  - `PUT` replace/update idempotent
  - `PATCH` partial update
  - `DELETE` remove
- **Status semantics check**:
  - Success: `200/201/204`
  - Client validation: `400/422`
  - Missing: `404`
  - Conflict/business rule: `409`
  - Avoid always-`200` envelopes for failures

### Step 3: Score and decide
Use this strict output:
- `RMM URI`: pass/fail
- `RMM method`: pass/fail
- `RMM status`: pass/fail
- `Overall`: pass/fail

Decision:
- **Compliant**: all 3 pass
- **Conditionally acceptable**: exactly 1 fail with migration plan
- **Reject**: 2+ fails or clear RPC regression

### Step 4: Suggest minimal fixes
When failing, propose smallest safe refactor:
- Path rename toward resource form
- Method correction
- Status code correction

## Output Requirements

Always report:
- Endpoints reviewed (method + path)
- RMM check matrix (URI/method/status)
- Final decision (Compliant / Conditionally acceptable / Reject)
- Required follow-up actions (if any)
