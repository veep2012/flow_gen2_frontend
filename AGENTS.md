# AGENTS

## Default Skill

For any API or database change or review, always apply the **api-db-guardian** skill to enforce compliance with `documentation/api_db_rules.md`.
For any API test creation/update/review, always apply the **test-scenario-guardian** skill to enforce scenario-first workflow and bidirectional sync between `documentation/test_scenarios/` and `tests/api/`.
For any documentation change or review, always apply the **docs-guardian** skill to enforce compliance with `documentation/_documentation_template.md` and `documentation/_documentation_standards.md`.

## Skills

- api-auto-tester: Run `make test` after API changes and iterate fixes until green. (file: skills/api-auto-tester/SKILL.md)
- test-scenario-guardian: Enforce scenario-first API test development and keep test scenarios synchronized with API tests. (file: skills/test-scenario-guardian/SKILL.md)
- docs-guardian: Keep documentation aligned with repository template and standards. (file: skills/docs-guardian/SKILL.md)
