---
name: api-db-guardian
description: Guard and review changes to backend API or PostgreSQL workflow architecture to ensure compliance with documentation/api_db_rules.md. Use when asked to modify API/DB logic, database functions, security/grants, workflow enforcement, or audit behavior, and when evaluating whether a change violates the DB-as-policy-engine model.
---

# API & DB Guardian

## Overview

Use this skill to **protect the existing backend–database contract**. The database is the policy engine; the API expresses intent only. Changes must comply with `documentation/api_db_rules.md`.

## Workflow (Required)

### Step 1: Classify the change
Choose exactly one:
- **API-only**
- **DB-only**
- **Cross-boundary**

### Step 2: Load the source of truth
- If working in this repo and `documentation/api_db_rules.md` exists, read it.
- Otherwise read `references/api_db_rules.md`.

### Step 3: Validate against guardrails
Check for violations:
- API bypasses workflow functions or mutates `core` tables directly.
- DB rules duplicated in API or weakened.
- Audit trails removed or made non-transactional.
- `app_user` granted DML on `core`, `ref`, or `audit`.
- Workflow status logic hardcoded instead of data-driven.

### Step 4: Decide
Pick one and state it explicitly:
- **Compliant**
- **Conditionally acceptable** (list constraints)
- **Reject** (architecture violation)

### Step 5: Explain in architectural terms
Reference the relevant sections of `api_db_rules.md` and explain **why** the decision preserves or violates the invariants.

## Response Requirements

- Be conservative and prefer correctness over convenience.
- If uncertain, say: “This change risks violating the architecture described in `documentation/api_db_rules.md`.”
- Do not propose shortcuts that bypass DB workflow enforcement.

## Resources

### references/
- `api_db_rules.md` — authoritative contract (fallback copy).
