# AGENTS

## Default Skill

For any API or database change or review, always apply the **api-db-guardian** skill to enforce compliance with `documentation/api_db_rules.md`.
For any documentation change or review, always apply the **docs-guardian** skill to enforce compliance with `documentation/DOCUMENTATION_TEMPLATE.md` and `documentation/DOCUMENTATION_STANDARDS.md`.

## Skills

- api-auto-tester: Run `make test` after API changes and iterate fixes until green. (file: skills/api-auto-tester/SKILL.md)
- docs-guardian: Keep documentation aligned with repository template and standards. (file: skills/docs-guardian/SKILL.md)
