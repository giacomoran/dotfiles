## Naming Conventions

Two subagents are available for naming convention work:

- **find-naming-issues** — explores code and reports violations (read-only)
- **fix-naming-issues** — fixes violations (can edit code)

When to use them:

- **Writing new code in a new project** — just read the naming-conventions skill, no need for subagents
- **Writing new code in an existing project** — try to be consistent with existing code, then run `find-naming-issues`, let me review, then run `fix-naming-issues`
- **Updating code in an existing project** — try to be consistent, run `find-naming-issues`, then `fix-naming-issues`
- **Reviewing a PR or diff** — run `find-naming-issues` scoped to the changed files
- **Renaming a concept across the codebase** — run `fix-naming-issues` directly
- **After a large refactor** — run `find-naming-issues` to catch naming drift
