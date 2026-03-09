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

## Avoid Fallbacks — Prefer Assertions and Errors

Prefer assertions and throwing errors over fallbacks and default values. Fallbacks hide bugs, create subtle footguns, and make code harder to reason about. Explicit failures make problems immediately visible and produce more trustworthy code.

- **Do** throw an error or assert when an unexpected condition occurs
- **Do** let functions fail loudly if preconditions aren't met
- **Don't** return default values, empty arrays, null, or 0 to paper over missing or invalid data
- **Don't** add try/catch that silently swallows errors or substitutes a fallback
- **Don't** use optional chaining (`?.`) or nullish coalescing (`??`) to silently handle cases that should never occur
- **Don't** add fallback logic in code to accommodate inconsistent or outdated data files — instead, flag the data file as the problem and let the user fix it

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

## Git Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format. The description must start with a verb in the imperative mood.

```
<type>: <description>
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `wip`

```
feat: add OAuth2 login flow
fix: handle missing user id in request
refactor: extract query builder into helper
chore: update dependencies
```

- Start the description with a verb: `add`, `fix`, `remove`, `update`, `refactor`, `extract`, `rename`, `move`, etc.
- Keep the description short and specific — what changed, not why
- Don't use scope (Conventional Commits supports `<type>(<scope>):`, but I think that's overkill)
- Use the `wip` type if we are not done with the implementation of changes in a branch that is not `main`

## Understand Before Touching

Before writing any code, understand what already exists. Find similar patterns in the codebase, read how they're built, and understand why. Don't introduce a new tool, pattern, or abstraction without a clear reason.

**Chesterton's fence:** if you don't know why code is there, don't remove it. The original author had a reason. Figure out the reason first.

## Readability Is the Primary Goal

After making the code work, the most important property of code is that it can be understood by someone else six months from now. Optimize for that reader above all else.

- Write code that is boring, obvious, and consistent with the rest of the codebase
- Prefer the same pattern used elsewhere in the project over a "better" pattern from outside
- Consistency across the codebase is a first-class goal — it's one of the main drivers of long-term understandability
- Clever code that requires mental effort to parse is a liability, not an asset
- If you need to open many files just to understand one small thing, that's a sign the code is too complex — not a reason to add more complexity on top.

## Comment Groups of Lines

Write a short comment above each logical group of lines explaining what the group does and why it's there. Don't comment every line — comment the intent of a block.

```ts
// Normalize the user's input before passing it to the parser
const inputNormalized = input.trim().toLowerCase();

// Build the lookup table once so repeated calls don't recompute it
const lookupByIdUser = buildLookup(users);
```

## Duplication Over Wrong Abstractions

Don't abstract until the pattern has appeared at least three times and you fully understand what varies and what doesn't. Premature abstractions are harder to remove than duplicate code.

- Copy-paste simple code rather than create a complex abstraction
- Three similar functions are better than one function with ten parameters
- A wrong abstraction forces every future caller to work around it — duplication just means updating two places

Wait. Watch the pattern repeat. Abstract only when the right shape becomes obvious.

## Simple Over Clever

Prefer the boring, straightforward solution over the elegant one. Complexity has a carrying cost — every clever trick must be understood, maintained, and debugged by future readers who weren't there when it was written.

- If there are two solutions and one is simpler, use the simpler one even if it's less "correct" in some abstract sense
- Working ugly code is better than beautiful broken code
- "Elegant" is not a compliment if it makes the code harder to follow

## Testing Strategy

- **Unit tests** for self-contained, complex logic with no dependencies (parsers, algorithms, pure functions)
- **Integration tests** at system boundaries — these catch the most real-world bugs
- **A small end-to-end suite** covering critical paths — keep it lean and always passing
- **Mock only at system boundaries** (external APIs, databases, file system) — never mock internal modules

Don't write tests just to have tests. A test that mocks everything and tests nothing real is noise.

## Architecture Principles

**Composition over inheritance.** Build behavior by combining small, focused pieces. Inheritance creates tight coupling and makes the shape of objects hard to reason about across a deep hierarchy.

**Explicit over implicit.** If something happens, it should be visible in the code. Magic — framework conventions, hidden side effects, implicit state — makes code harder to trace and debug.

**Locality of behavior.** Code that does a thing should live close to the thing it acts on. Avoid action-at-a-distance where a change in one place has invisible effects somewhere else. A reader should be able to understand a piece of behavior by reading the code around it, not by tracing execution across many files.
