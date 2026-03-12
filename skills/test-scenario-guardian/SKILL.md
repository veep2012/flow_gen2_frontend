---
name: test-scenario-guardian
description: Enforce scenario-first API verification development with strict bidirectional traceability between documentation/test_scenarios/*.md and automated verification artifacts such as tests/api/**/*.py or scripts/*.sh. Use for API test creation, updates, and reviews.
---

# Test Scenario Guardian

## Overview

Use this skill to keep API test scenarios and automated API verification tightly synchronized.

Core rule:
1. Define or update scenarios first in `documentation/test_scenarios/`.
2. Implement or update automated API verification in the appropriate executable artifact.
3. Ensure bidirectional links so changing one requires updating the other.
4. Treat scenario documentation as the single source of truth for expected behavior.

## When To Use

Use for any of the following:
- New API endpoint tests
- Updates to existing API tests
- New or updated shell-based API smoke/integration checks
- Test reviews where behavior/coverage changes
- Scenario document changes that affect test behavior

## Workflow (Required)

### Step 1: Create/Update scenario doc first
- Ensure a scenario file exists in `documentation/test_scenarios/`.
- Scenario filenames must be lowercase only (no uppercase characters).
- Add `Document Control` metadata updates.
- Define stable scenario IDs (for example: `TS-DL-001`).
- For each scenario include:
  - intent
  - setup/preconditions
  - request/action
  - expected response/assertions
  - cleanup (if required)

### Step 2: Implement automated verification from scenario IDs
- Add/update the executable verification artifact in the appropriate location.
- Prefer `tests/api/` for pytest-based API checks.
- Allow shell-based or other executable smoke checks (for example `scripts/*.sh`) when the behavior depends on external runtime topology and is not practical to validate in pure pytest alone.
- Each automated verification artifact must reference scenario IDs in code, comments, docstrings, or adjacent metadata.
- Keep assertions aligned to scenario acceptance criteria.
- When behavior differs between docs and verification artifacts, update verification to match docs unless the user explicitly asks to revise docs first.

### Step 3: Enforce bidirectional traceability
- In scenario docs, add an **Automated Test Mapping** section with the concrete executable artifact names and entrypoints.
- In automated verification artifacts, add a mapping to scenario IDs and scenario doc path where practical.
- Add/maintain a lightweight traceability check when feasible that fails when:
  - a mapped scenario ID is missing from the scenario doc
  - a mapped automated verification entry is missing from the scenario doc mapping section

### Step 4: Validate and tighten
- If automated verification changed, update scenario docs in the same change.
- If scenario docs changed, update automated verification in the same change.
- Reject partial updates that only modify one side when linkage is affected.
- Resolve ambiguity by tightening the scenario doc first, then update tests accordingly in the same change.
- Verify `documentation/` has no uppercase markdown filenames before finalizing:
  - `find documentation -type f -name '*.md' | rg '[A-Z]'`

## Output Requirements

Always report:
- Scenario file(s) updated
- Verification artifact(s) updated
- Traceability checks added/updated
- Any intentional gaps (manual-only scenarios vs automated coverage)
