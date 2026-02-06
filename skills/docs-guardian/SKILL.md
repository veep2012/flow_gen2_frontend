---
name: docs-guardian
description: Standardize and review repository documentation against documentation/DOCUMENTATION_TEMPLATE.md and documentation/DOCUMENTATION_STANDARDS.md. Use when creating, updating, or reviewing files in documentation/.
---

# Docs Guardian

## Overview

Use this skill to keep project documentation consistent, complete, and aligned with:
- `documentation/DOCUMENTATION_TEMPLATE.md`
- `documentation/DOCUMENTATION_STANDARDS.md`

## Workflow (Required)

### Step 1: Classify the doc task
Choose one:
- **New document**
- **Update existing document**
- **Review existing document**

### Step 2: Load standards and template
- Read `documentation/DOCUMENTATION_STANDARDS.md`.
- Read `documentation/DOCUMENTATION_TEMPLATE.md`.

### Step 3: Validate required structure
For each target file in `documentation/`:
- Confirm required sections from standards exist.
- Confirm one H1 heading only.
- Confirm `Document Control` is present with status, owner, and dates.
- Confirm `References` section exists.

### Step 4: Normalize and tighten content
- Keep wording implementation-focused and concise.
- Use explicit requirement language (`must`, `should`, `may`) where applicable.
- Remove sections that are not applicable; do not leave placeholder text in final docs.
- Keep Mermaid diagrams only when they add clarity.

### Step 5: Report result
State one outcome:
- **Compliant**
- **Updated to compliant**
- **Partially compliant** (list exact gaps)

## Response Requirements

- When editing docs, mention which sections were added or normalized.
- When reviewing only, provide a checklist of pass/fail items from the standards.
- Do not invent requirements that conflict with repository standards.

