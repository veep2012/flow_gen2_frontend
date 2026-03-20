# Documentation Standards

This file defines the unified format for documents in `documentation/`.
Naming rules are defined in `documentation/_naming_convention.md`.
Navigation starts from `documentation/_documentation-index.md`.

## 1. File Naming
- Use lowercase with underscores: `topic_name.md`.
- Uppercase letters in Markdown filenames under `documentation/` are not allowed.
- Prefer descriptive names over abbreviations.
- Keep one primary topic per file.
- For helper/control files (standards, templates, conventions), prefix with `_`:
  - `_documentation_template.md`
  - `_documentation_standards.md`
  - `_naming_convention.md`
  - `_documentation-index.md`

## 2. Required Sections
Every new document should include at minimum:
1. `# Title`
2. `## Document Control`
3. `## Change Log`
4. `## Purpose`
5. `## Scope`
6. `## Design / Behavior`
7. `## Edge Cases`
8. `## References`

Use `documentation/_documentation_template.md` as the starting point.
`## Change Log` must be placed immediately after `## Document Control`.

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
- Add a `Change Log` section to every document.
- Keep `Change Log` near the top: immediately after `Document Control`.
- Add a new entry for each new document version.
- Record version/date and concise summary of what changed.
- Keep the newest entry first.
- Keep at most one `Change Log` entry per calendar date in each document.
- If multiple updates happen on the same date, merge them into the existing entry for that date instead of adding another row.
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
5. Add or update `Change Log` as the first content section after `Document Control`.
6. Add the new file to `documentation/_documentation-index.md`.

## 10. Naming Verification
- Before finalizing documentation changes, run:
  - `find documentation -type f -name '*.md' | rg '[A-Z]'`
- Expected result: no output.
- If any path is returned, rename it to lowercase and update all references in the same change.
