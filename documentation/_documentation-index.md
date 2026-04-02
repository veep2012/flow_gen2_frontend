# Documentation Index

## Purpose
- Provide a single entry point for all files in `documentation/`.
- Reduce navigation chaos by grouping files by purpose.
- Track ownership/status quickly using each document's `Document Control` section.

## Repository Split
- `repo_split/repository_split_requirements_sub_story.md` - Draft numbered sub-story defining the requirement baseline and target operating model for frontend/backend repository separation.
- `repo_split/repository_split_technical_vision.md` - Draft future-state technical vision and to-be architecture for frontend/backend repository separation.
- `repo_split/repository_split_phase_1_foundation_and_governance.md` - Exact technical instruction for phase 1 repository creation, governance setup, and ownership controls.
- `repo_split/repository_split_phase_2_registry_and_artifact_model.md` - Exact technical instruction for phase 2 internal and external registry setup, image rules, provenance, and fallback.
- `repo_split/repository_split_phase_3_repository_migration_and_build_enablement.md` - Exact technical instruction for phase 3 code redistribution, cleanup, contract preservation, and independent build/publish enablement.
- `repo_split/frontend_repository_phase_3_prune_record.md` - Frontend repository migration record summarizing removed backend assets, rewritten frontend entrypoints, and remaining integration assumptions.

## Standards and Templates
- `_documentation_standards.md` - Required structure and writing rules.
- `_documentation_template.md` - Base template for new documents.
- `_naming_convention.md` - Filename rules.
- `_documentation-index.md` - This index file.

## Maintenance Rules
- Add every new `documentation/*.md` file to this index in the same change.
- Keep entries lowercase to match naming convention.
- Keep helper/control files prefixed with `_`.
- Use `-` bullets for all index entries.
