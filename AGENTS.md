# AGENTS

## Default Skill

For any API or database change or review, always apply the **api-db-guardian** skill to enforce compliance with `documentation/api_db_rules.md`.
For any API change or API-related database change/review, always apply the **api-auto-tester** skill to run `make test` and iterate until green.
For any API endpoint design change or review, always apply the **api-rmm-guard** skill to prevent regressions below Richardson Maturity Model Level 2.
For any backend Python (`*.py`) change or review, always apply the **backend-doc-sync** skill to keep backend implementation and repository documentation synchronized.
For any API test creation/update/review, always apply the **test-scenario-guardian** skill to enforce scenario-first workflow and bidirectional sync between `documentation/test_scenarios/` and `tests/api/`.
For any documentation change or review, always apply the **docs-guardian** skill to enforce compliance with `documentation/_documentation_template.md` and `documentation/_documentation_standards.md`.
For any development task where non-blocking issues are found but intentionally deferred, always apply the **tech-debt** skill to record debt in `tech-debt/<YYYY-MM-DD>.md`.
For any explicit user request to create a commit, always apply the **commiter** skill.

## Skills

- api-auto-tester: Run `make test` after API changes and iterate fixes until green. (file: skills/api-auto-tester/SKILL.md)
- api-rmm-guard: Guard API design against regressions below Richardson Maturity Model Level 2. (file: skills/api-rmm-guard/SKILL.md)
- backend-doc-sync: Require documentation updates whenever backend Python code changes. (file: skills/backend-doc-sync/SKILL.md)
- test-scenario-guardian: Enforce scenario-first API test development and keep test scenarios synchronized with API tests. (file: skills/test-scenario-guardian/SKILL.md)
- docs-guardian: Keep documentation aligned with repository template and standards. (file: skills/docs-guardian/SKILL.md)
- monthly-doc-actualizer: Run daily due checks and trigger full code-first documentation actualization against the current implementation after cadence threshold. (file: skills/monthly-doc-actualizer/SKILL.md)
- tech-debt: Capture deferred technical debt items into dated markdown files under `tech-debt/`. (file: skills/tech-debt/SKILL.md)
- commiter: Create commit/push flow with standardized commit message format on explicit commit requests. (file: skills/commiter.md)
