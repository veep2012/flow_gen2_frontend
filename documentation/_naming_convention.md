# Documentation Naming Convention

## Purpose
Define filename rules for all Markdown files in `documentation/`.

## Rules
- Use lowercase only.
- Use underscores as word separators.
- Use `.md` extension for Markdown files.
- Use a leading underscore for helper/control files that are not product/feature documentation:
  - standards
  - templates
  - conventions
  - indexes

## Examples
- Documentation files:
  - `api_interfaces.md`
  - `distribution_list_feature.md`
  - `notifications_and_dls.md`
- Helper/control files:
  - `_documentation_template.md`
  - `_documentation_standards.md`
  - `_naming_convention.md`
  - `_documentation-index.md`

## Migration Guidance
- When touching an existing file, rename it to this convention if safe.
- Update all references in docs, skills, and `AGENTS.md` in the same change.
