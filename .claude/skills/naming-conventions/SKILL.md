---
name: naming-conventions
description: Code naming patterns
---

Naming is one of the most important things in programming. I care deeply about getting it right. These conventions apply across all programming languages — examples use TypeScript and Python but the principles are universal. Understand the intent behind each rule, not just the specific examples.

If any convention is unclear, read `EXAMPLES.md` in this directory for concrete examples from real projects.

## Noun-First Variables

The primary noun comes first, followed by qualifiers that narrow it down. This applies to variables, constants, parameters, fields, columns — everything that holds a value.

- `idUser` not `userId`, `id_note` not `note_id`
- `pathOutput` not `outputPath`, `path_dataset` not `dataset_path`
- `tsCreated` not `createdTs`, `ts_first_review_ms` not `first_review_ts`

**Qualifiers build outward from the noun:**

- `idUser` → `idUserAuthor` (narrowing which user)
- `action` → `actionChunkPending` → `actionChunkActive` (adding state)
- `message` → `messageModel0` → `inputToolCall0MessageModel0` (adding position in hierarchy)

**Pluralization applies to the noun only:**

- `idsNote` not `idsNotes`, `ids_note` not `ids_notes`
- `datesIso` not `datesIsos`

**The prefix IS the noun — it tells you what kind of value this is:**

| Prefix | What it holds |
|--------|---------------|
| `id` / `ids` | Identifiers |
| `idx` | Positional index |
| `ix` | Fractional/sort index |
| `cnt` / `count` | Count |
| `ts` | Timestamp |
| `date` | Date |
| `millis` | Epoch milliseconds |
| `path` | File path |
| `url` | URL |
| `key` / `prefix` | Key or key prefix |
| `name` | Name string |
| `version` | Version identifier |
| `df` | DataFrame |
| `dict` / `record` | Dictionary / key-value map |
| `array` | Array (when type isn't obvious) |
| `option` | Optional/nullable wrapper |
| `bytes` / `blob` / `buffer` | Binary data |
| `data` | Data structure / payload |
| `settings` | Configuration object |
| `content` | Content payload |
| `is` | Boolean flag |
| `event` | Event |
| `thread` | Thread |
| `state` | State container |
| `elem` | DOM element |
| `template` | Template |

## Verb-First Functions

Functions start with a verb. The noun-first rule still applies within the rest of the name.

- `computeRetentionRate` not `retentionRateCompute`
- `extract_reviews_user` not `extract_user_reviews`
- `fetchDataUser` not `fetchUserData`
- `generateItemsAndCreateEntries` (compound verbs are fine)

**Common verb prefixes:**

| Prefix | Usage |
|--------|-------|
| `make` | Factory / constructor |
| `create` / `delete` / `update` | CRUD |
| `get` / `set` | Retrieval / assignment |
| `compute` | Derivation from inputs |
| `generate` | Content generation |
| `convert` / `to` | Format conversion |
| `process` / `extract` | Data transformation |
| `render` | Rendering |
| `is` | Type predicate |
| `log` | Logging |

**File names mirror this:** entity files are noun-based (`user.ts`, `deck.ts`), command files are verb-first hyphenated (`create-user.ts`, `get-user-by-id.ts`), utility files use `utils-` prefix (`utils-date-time.ts`).

## One Name Per Concept

Each domain concept gets **exactly one canonical name**. That name is used everywhere — code, database, API, config, documentation. Never introduce a synonym.

For example, if the concept is called "user", it's always "user" — never "account", "member", or "profile" in some places. If it's called "order", it's always "order" — never "purchase" or "transaction" elsewhere. Pick one word and use it everywhere.

**Minimize vocabulary. Every new name is a cost.** When you need a variant, qualify the existing name — don't invent a new one:

- A lightweight version of `User`? → `UserMini`, not `Profile` or `UserSummary`
- An ID-only reference to `User`? → `IdUser`, not `UserRef`
- A specific type of `Job`? → `JobGenerateCards`, not `CardGenerationTask`
- A draft of an entity? → `DraftCreateOrder`, not `PendingOrder`

The pattern: **same root noun + qualifier**, never a different root noun for the same concept.

**This applies across every boundary** — the underlying name is always the same, only mechanical case conversions change the form:

| Boundary | Form | Example |
|----------|------|---------|
| Code (JS/TS) | camelCase | `idUser` |
| Code (Python) | snake_case | `id_user` |
| Database column | snake_case | `id_user` |
| API URL | kebab-case | `/v1/get-user` |
| Storage key | PascalCase prefix | `"User/abc123"` |
| Documentation | lowercase | "user" |

If you see a concept referred to by two different names anywhere in the project — code, comment, config, docs — that's a bug.

## Nominal Consistency

Once a value has a name, **that exact name follows it through every layer and call site**. Never rename a value as it flows through the system.

### Rule 1: Argument names match parameter names

The variable you pass at a call site must have the same name as the parameter it binds to. This makes data flow traceable — you can search for a name and find every place it's used.

```
// Definition
const renderChart = (args: { dataYear: DataYear; configChart: ConfigChart }) => ...

// Call site — names match exactly, enabling shorthand
const chart = renderChart({ dataYear, configChart })
//                           ↑ same name as parameter
```

When you can't use shorthand (e.g., the value comes from a different context), the right-hand side should still make the mapping clear:

```
service.createOrder({ idUser: ctx.idUser, tsCreated: tsNow })
//                    ↑ parameter   ↑ clear origin
```

### Rule 2: Field names survive across layers

When data crosses boundaries (function → function, service → API, code → database), field names don't change. The same field is `idUser` in the entity definition, `idUser` in the service call, `idUser` in the API handler, and `id_user` in the database (mechanical case conversion only).

```
// Entity definition
{ idUser: Id, tsCreated: DateTime }

// Service call — same names
service.createOrder({ idUser, tsCreated: tsNow })

// Database — mechanical snake_case conversion only
INSERT INTO "order" (id_user, ts_created) ...
```

### Rule 3: Disambiguation uses indexed suffixes, not new names

When multiple values of the same type exist, use positional suffixes — don't invent distinct names:

- `messageModel0`, `messageModel1` (not `firstMessage`, `secondMessage`)
- `inputToolCall0MessageModel0` (hierarchical: input → toolCall[0] → messageModel[0])

The goal: **reading any line of code, you can trace the value back to its origin by searching for its name.** Renaming breaks traceability.

## Library Interface Consistency

When interfacing with external libraries, **preserve the library's naming conventions** for:

- Function parameters that match library APIs
- Dict keys / column names that follow library conventions
- Variables passed directly to library functions
- Standard framework naming (e.g., `device` for PyTorch, `con` for DuckDB)

Use noun-first naming for internal code, but maintain consistency at library boundaries.

## File/Folder Prefixes

- `bak` prefix/suffix: backup files and folders, ignore unless explicitly asked
- `tmp` prefix/suffix: temporary files and folders, ignore unless explicitly asked
- `zxtra` prefix/suffix: extra files and folders (work-in-progress or uncertain), generally ignore
