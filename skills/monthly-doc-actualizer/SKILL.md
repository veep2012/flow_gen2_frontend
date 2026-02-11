---
name: monthly-doc-actualizer
description: Run daily documentation freshness checks and trigger full documentation actualization when 30+ days have passed since the last full run. Use when maintaining periodic doc/code alignment for `documentation/*.md`.
---

# Monthly Doc Actualizer

## Overview

Use this skill to enforce periodic documentation refresh with a lightweight daily check and a full monthly actualization when due.

State is tracked in:
- `documentation/_documentation_actualization_state.md`

Helper script:
- `skills/monthly-doc-actualizer/scripts/check_due.py`

## Workflow (Required)

### Step 1: Run daily due check
- Run:
  - `python3 skills/monthly-doc-actualizer/scripts/check_due.py --state-file documentation/_documentation_actualization_state.md --mark-check`
- Read output fields:
  - `DUE=true|false`
  - `LAST_FULL_ACTUALIZATION`
  - `NEXT_DUE_DATE`
  - `DAYS_SINCE_FULL`

### Step 2: If not due
- Stop after the check.
- Report that monthly actualization is not required yet.

### Step 3: If due
- Run full documentation actualization for `documentation/*.md`:
  - verify docs vs implementation (`api/routers`, `api/schemas`, `ci/init/*.sql`, `tests/api`)
  - fix stale contracts/examples/schema references
  - normalize `Document Control` metadata (`Last Updated`, `Version`) in modified docs
  - keep `documentation/_documentation-index.md` aligned for any added/renamed docs
- After successful update, mark completion:
  - `python3 skills/monthly-doc-actualizer/scripts/check_due.py --state-file documentation/_documentation_actualization_state.md --mark-full`

### Step 4: Validate
- Run:
  - `find documentation -type f -name '*.md' | rg '[A-Z]'`
- Expected: no output.

## Output Requirements

Always report:
- Whether monthly run was due
- Files updated
- New next due date
- Any unresolved ambiguity or manual follow-up
