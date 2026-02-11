# Documentation Actualization State

## Document Control
- Status: Approved
- Owner: Backend Team
- Reviewers: API maintainers
- Created: 2026-02-11
- Last Updated: 2026-02-11
- Version: v1.0

## Purpose
Track periodic documentation-refresh cadence for repository docs.

## Scope
- In scope:
  - Daily freshness checks.
  - Last full documentation actualization date.
  - Cadence threshold for the next full run.
- Out of scope:
  - Detailed change logs for each documentation update.

## Design / Behavior
- Last Check: 2026-02-11
- Last Full Actualization: 2026-02-11
- Cadence Days: 30

Use `skills/monthly-doc-actualizer/scripts/check_due.py` to evaluate due status and update these fields.

## Edge Cases
- If dates are manually edited to invalid format, due checks must fail fast.
- If cadence is set to non-positive value, due checks must fail fast.

## References
- `skills/monthly-doc-actualizer/SKILL.md`
- `skills/monthly-doc-actualizer/scripts/check_due.py`
