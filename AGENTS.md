# AGENTS

## Repository Boundary

- This repository owns frontend assets only.
- Keep changes within frontend-owned paths such as `ui/`, `scripts/local-ui-container.sh`, `scripts/local-ui-runtime.sh`, `ci/Dockerfile.ui`, `README.md`, and `documentation/repo_split/`.
- Do not reintroduce backend runtime code, backend build logic, backend deployment manifests, backend-only tests, or backend-owned contract sources.
- Consume backend integration through configuration only, primarily `VITE_API_BASE_URL` and `VITE_AUTH_START_URL`.

## Default Skill

For any documentation change or review, always apply the **docs-guardian** skill to enforce compliance with `documentation/_documentation_template.md` and `documentation/_documentation_standards.md`.
For any explicit user request to create a commit, always apply the **commiter** skill.

## Skills

- docs-guardian: Keep documentation aligned with repository template and standards. (file: `skills/docs-guardian/SKILL.md`)
- commiter: Create commit/push flow with standardized commit message format on explicit commit requests. (file: `skills/commiter.md`)

## Documentation

- Keep split and migration records under `documentation/repo_split/`.
- Remove or rewrite any documentation that assumes this repository still owns backend code or a combined-repository build path.
