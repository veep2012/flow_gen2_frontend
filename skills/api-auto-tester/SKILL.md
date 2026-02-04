---
name: api-auto-tester
description: Run `make test` after API changes and, on failure, iterate fixes until tests are green. Use this skill whenever API routes, request/response schemas, or related validation/business logic are modified.
---

# API Auto Tester

## Overview

This skill enforces running `make test` after API changes and iterating on fixes until tests pass.

## When To Use

Use this skill for any API change, including:
- Route handlers or routers
- Request/response schemas
- Validation or business logic tied to API endpoints
- API-related DB changes

## Workflow

1. **Detect API changes**
   - If the user’s request includes API changes, proceed with this skill.
   - If DB or API changes are involved, also apply the `api-db-guardian` skill per repo rules.

2. **Make the requested code changes**
   - Implement the change with minimal, focused edits.
   - Add or update tests if needed.

3. **Run tests**
   - Run `make test` from repo root.
   - If `make test` fails, iterate: diagnose, fix, and re-run until green.

4. **Report results**
   - Summarize failures and fixes.
   - If tests cannot be run, state why and what would be needed.

## Output Expectations

Always report:
- Whether `make test` was run
- Any failures and the fixes applied
- Final test status
