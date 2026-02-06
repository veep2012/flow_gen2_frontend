# Documentation Standards

This file defines the unified format for documents in `documentation/`.
Naming rules are defined in `documentation/_naming_convention.md`.

## 1. File Naming
- Use lowercase with underscores: `topic_name.md`.
- Prefer descriptive names over abbreviations.
- Keep one primary topic per file.
- For helper/control files (standards, templates, conventions), prefix with `_`:
  - `_documentation_template.md`
  - `_documentation_standards.md`
  - `_naming_convention.md`

## 2. Required Sections
Every new document should include at minimum:
1. `# Title`
2. `## Document Control`
3. `## Purpose`
4. `## Scope`
5. `## Design / Behavior`
6. `## Edge Cases`
7. `## References`

Use `documentation/_documentation_template.md` as the starting point.

## 3. Header and Style Rules
- Use one H1 (`#`) per file.
- Use sentence case or title case consistently within a file.
- Use bullet lists for rules and requirements.
- Keep paragraphs short and implementation-focused.
- Prefer explicit terms like `must`, `should`, `may` for requirement strength.

## 4. Status and Ownership
- `Document Control` must include owner, status, and dates.
- Allowed statuses: `Draft`, `Review`, `Approved`, `Deprecated`.
- Update `Last Updated` when behavior or contract changes.

## 5. API and DB Content
- API docs should include method/path, request/response examples, and expected errors.
- DB docs should include entities/tables, key fields, constraints, and migration notes.
- If behavior changes impact API/DB contracts, link related rules and source files.

## 6. Diagrams
- Use Mermaid for flows/architecture when it improves clarity.
- Keep diagrams minimal and aligned with the text.
- If a diagram conflicts with text, text is source of truth until updated.

## 7. Change Management
- Add a `Change Log` section for substantial documents.
- Record version/date for notable updates.
- Keep historical decisions in document history or linked ADRs.

## 8. Migration of Existing Docs
- Do not rewrite everything at once.
- When touching an existing doc, align it to the template incrementally:
  1. Add `Document Control`
  2. Normalize sections
  3. Add missing edge cases/references

## 9. Quick Start
1. Copy `documentation/_documentation_template.md`.
2. Fill mandatory sections first.
3. Remove non-applicable optional sections.
4. Add links to related docs and implementation files.
