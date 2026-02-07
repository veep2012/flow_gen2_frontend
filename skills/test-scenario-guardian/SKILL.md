---
name: test-scenario-guardian
description: Enforce scenario-first API test development with strict bidirectional traceability between documentation/test_scenarios/*.md and tests/api/**/*.py. Use for API test creation, updates, and reviews.
---

# Test Scenario Guardian

## Overview

Use this skill to keep API test scenarios and automated API tests tightly synchronized.

Core rule:
1. Define or update scenarios first in `documentation/test_scenarios/`.
2. Implement or update API tests in `tests/api/`.
3. Ensure bidirectional links so changing one requires updating the other.
4. Treat scenario documentation as the single source of truth for expected behavior.

## When To Use

Use for any of the following:
- New API endpoint tests
- Updates to existing API tests
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

### Step 2: Implement API tests from scenario IDs
- Add/update tests under `tests/api/`.
- Each test must reference scenario IDs in code (constant, docstring, or comment).
- Keep assertions aligned to scenario acceptance criteria.
- When behavior differs between docs and tests, update tests to match docs unless the user explicitly asks to revise docs first.

### Step 3: Enforce bidirectional traceability
- In scenario docs, add an **Automated Test Mapping** section with test function names.
- In tests, add a mapping to scenario IDs and scenario doc path.
- Add/maintain a lightweight check test that fails when:
  - a mapped scenario ID is missing from the scenario doc
  - a mapped test function is missing from the scenario doc mapping section

### Step 4: Validate and tighten
- If tests changed, update scenario docs in the same change.
- If scenario docs changed, update tests in the same change.
- Reject partial updates that only modify one side when linkage is affected.
- Resolve ambiguity by tightening the scenario doc first, then update tests accordingly in the same change.
- Verify `documentation/` has no uppercase markdown filenames before finalizing:
  - `find documentation -type f -name '*.md' | rg '[A-Z]'`

## Output Requirements

Always report:
- Scenario file(s) updated
- Test file(s) updated
- Traceability checks added/updated
- Any intentional gaps (manual-only scenarios vs automated coverage)
