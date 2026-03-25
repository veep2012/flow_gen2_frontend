# Story Template

## Document Control
- Status: Draft
- Owner: Product / Engineering
- Reviewers: Product owner, tech lead
- Created: 2026-03-25
- Last Updated: 2026-03-25
- Version: v0.1
- Related Tickets: N/A

## Change Log
- 2026-03-25 | v0.1 | Initial draft with lightweight parent-story and sub-story templates.

## Purpose
Provide a lightweight and reusable template for initiative parent stories and numbered sub-stories.

## Scope
- In scope:
  - parent story template
  - sub-story template
  - concise field guidance
- Out of scope:
  - issue tracker workflow rules
  - estimation rules
  - sprint planning rules

## Design / Behavior
Use the parent story to describe the business goal and overall direction. Use numbered sub-stories to define concrete deliverables that can be implemented and verified independently.

### Parent story template
```md
# <Parent Story Title>

## Description
As a <team or organization>, we want <target outcome> so that <business value>.

This parent story defines the overall objective and scope for the initiative. Detailed requirements, design decisions, implementation steps, and rollout work are expected to be delivered through numbered sub-stories.
```

### Sub-story template
```md
# <N>. <Sub-Story Title>

## Description
As a <role or team>, we want <specific outcome> so that <practical value>.

This sub-story covers <brief scope statement>. It should produce a clear and reviewable outcome that contributes directly to the parent story.

## Acceptance Criteria
- <criterion>
- <criterion>

## Definition of Done
- Implementation or document changes are completed.
- Relevant documentation is updated.
- Relevant review is completed.
- Open questions affecting delivery are resolved or explicitly recorded.
```

### Usage guidance
- Keep the parent story broad and outcome-focused.
- Keep sub-stories small enough to review and close independently.
- Use numbered sub-stories such as `0. Define Requirements`, `1. Define Architecture`, `2. Implement Access Model`.
- Keep descriptions concise and avoid embedding low-level tasks into story descriptions.
- Put story-specific validation into `Acceptance Criteria`.
- Keep `Definition of Done` short and reusable across stories.

## Edge Cases
- A story is too broad to complete in one iteration: split it into additional numbered sub-stories.
- A sub-story becomes design-heavy: move detailed requirements or design content into linked documentation instead of overloading the story text.
- A team-specific rule conflicts with this template: the team rule takes precedence, but the structure should stay close to this template where practical.

## References
- `documentation/_documentation_template.md`
- `documentation/_documentation_standards.md`
- `documentation/_documentation-index.md`
