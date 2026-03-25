---
name: story-guardian
description: Standardize story creation, refinement, and review against `documentation/story_template.md`. Use when creating or updating parent stories, numbered sub-stories, acceptance criteria, or definitions of done.
---

# Story Guardian

## Overview

Use this skill whenever work involves creating, refining, or reviewing stories for initiatives, parent stories, or numbered sub-stories.

Core rule:
1. Story content must follow `documentation/story_template.md`.
2. Story wording must stay concise and outcome-focused.
3. Parent stories must remain broad; detailed delivery belongs in numbered sub-stories.
4. Acceptance criteria must stay story-specific.
5. Definition of Done must stay short and reusable.

## When To Use

Use for any of the following:
- Creating a new parent story.
- Creating a new numbered sub-story.
- Refining story title or description.
- Writing or tightening acceptance criteria.
- Writing or tightening Definition of Done.
- Reviewing existing story text for consistency.

## Workflow (Required)

### Step 1: Classify the story work
Choose one:
- **Parent story**
- **Sub-story**
- **Story review**

### Step 2: Load the template and standards
- Read `documentation/story_template.md`.
- If the story content is stored in `documentation/`, also apply:
  - `documentation/_documentation_template.md`
  - `documentation/_documentation_standards.md`
  - `documentation/_documentation-index.md`

### Step 3: Apply structure rules
- Parent stories must contain a concise title and broad description.
- Sub-stories should use numbered titles such as `0. Define Requirements`.
- Keep descriptions focused on outcome and scope, not implementation tasks.
- Use `Acceptance Criteria` for story-specific validation.
- Use `Definition of Done` for short reusable completion gates.

### Step 4: Tighten content
- Prefer simple business language over technical detail unless the user asks for more detail.
- Avoid embedding long task lists into the description.
- Keep requirements or architecture detail in linked documents when the story becomes too dense.
- Split stories when one story covers multiple independently deliverable outcomes.

### Step 5: Report result
State one outcome:
- **Compliant**
- **Updated to compliant**
- **Partially compliant** (list exact gaps)

## Output Requirements

Always report:
- Story type handled
- Template sections created or normalized
- Whether the story remains broad enough or should be split
