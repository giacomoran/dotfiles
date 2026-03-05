---
name: code
description: >
  Coding conventions and guidelines. Load this skill whenever reading or writing code.
---

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

## Prefer Flat If Branches Over Else

Avoid `else` and `else if`. Instead, write each branch as an independent `if` and terminate with a `throw` for the unreachable case. This makes every branch explicit and exhaustive, and avoids implicit fallthrough logic that's easy to misread.

```ts
// Preferred
if (status === "active") { ... }
if (status === "inactive") { ... }
throw new Error(`Unreachable: unexpected status ${status}`)

// Avoid
if (status === "active") { ... }
else { ... }
```

## Prefer Verbose Conditions Over Nesting

Prefer longer, explicit conditions — even with duplication — over nested `if` branches. Flat structure is easier to read and reason about than nested logic.

```ts
// Preferred
if (isAdmin && hasPermission && isActive) { ... }
if (isAdmin && hasPermission && !isActive) { ... }
if (isAdmin && !hasPermission) { ... }
throw new Error("Unreachable")

// Avoid
if (isAdmin) {
  if (hasPermission) {
    if (isActive) { ... }
    else { ... }
  } else { ... }
}
```

Duplicating a condition across branches is acceptable — even desirable — when it makes each branch self-contained and independently readable.

## Avoid Fallbacks — Prefer Assertions and Errors

Prefer assertions and throwing errors over fallbacks and default values. Fallbacks hide bugs, create subtle footguns, and make code harder to reason about. Explicit failures make problems immediately visible and produce more trustworthy code.

- **Do** throw an error or assert when an unexpected condition occurs
- **Do** let functions fail loudly if preconditions aren't met
- **Don't** return default values, empty arrays, null, or 0 to paper over missing or invalid data
- **Don't** add try/catch that silently swallows errors or substitutes a fallback
- **Don't** use optional chaining (`?.`) or nullish coalescing (`??`) to silently handle cases that should never occur
- **Don't** add fallback logic in code to accommodate inconsistent or outdated data files — instead, flag the data file as the problem and let the user fix it
