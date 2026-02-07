# Naming Convention Examples

Concrete examples collected from real projects. Append new entries as they come up.

---

## Noun-First Variables

### snake_case (Python)

- IDs: `id_card`, `ord_card`, `ids_card_suspended`, `id_note`, `ids_note`
- Indices: `idx_user`, `idx_day`, `idx_review`
- Counts: `cnt_reviews`, `cnt_reviews_again`, `cnt_reviews_total`
- Timestamps: `ts_first_review_ms`, `ts_last_review_ms`
- Dates: `date_local`, `date_first_review`
- Paths: `path_dataset`, `path_output`, `path_parquet`
- DataFrames: `df_reviews`, `df_cards`, `df_retention`
- Dicts: `dict_review`
- Intervals: `interval_days`, `interval_ms`
- Booleans: `is_suspended`, `is_first_review`

### camelCase (JS/TS)

**From rember:**
- IDs: `idUser`, `idDeck`, `idRemb`, `idJob`, `idUserAuthor`
- Timestamps: `tsCreated`, `tsUpdated`
- URLs: `urlPicture`
- Names: `nameTable`, `nameTableReplicache`
- Data: `dataStreak`, `dataSubscriptionStripe`, `dataImage`, `dataYear`
- Settings: `settingsScheduler`, `settingsDefault`
- Content: `contentRemb`, `contentDraftCreateRembs`
- Keys: `keyApiKey`, `prefixKeyReplicacheClient`
- Versions: `versionSchema`, `versionReplicache`
- Messages: `messagesSqs`

**From rember-mcp:**
- Notes: `notesRember`
- Messages (indexed): `messageModel0`, `messageModel1`
- Parts (hierarchical): `partText0MessageModel1`, `partsToolCallMessageModel0`
- Inputs (hierarchical): `inputToolCall0MessageModel0`
- API keys: `apiKey`, `apiKeyEnc`

**From anki-wrapped:**
- Container types: `arrayDateIso`, `recordHeatmap`, `optionDataImage`, `optionCountReviews`
- Binary: `bytesCollectionAnki21b`, `bytesPng`, `blobPng`
- Temporal: `millisStart`, `millisEnd`, `dateStart`, `dateEnd`, `dateIso`
- State: `stateImage$`, `stateCollectionAnki$`
- Elements: `elemAnchor`
- Templates: `templateBackgroundStarryNight`, `templateHeatmap`
- Year-qualified: `dataYear2024`, `dataYear2025`

**From robotics project:**
- Observations: `dictObs`, `proprioObs`, `dictObsCurrent`
- Actions: `actionChunkPending`, `actionChunkActive`, `tensorAction`
- Events: `eventShutdown`, `eventInferenceRequested`
- Counts: `countActions`, `countTotalActions`
- Indices: `idxChunk`, `idxFrame`
- Threads: `threadInference`, `threadActor`
- Trackers: `trackerLatency`
- Timesteps: `timestepObs`, `timestepAction`
- Booleans: `isInferenceRunning`, `isControlFrame`

---

## Verb-First Functions

### snake_case (Python)

- `extract_reviews_user`, `compute_retention_rate`

### camelCase (JS/TS)

**Factories (make):**
- `makeRember`, `makeServerMCP`, `makeJsonSchema`
- `makeCreateUser`, `makeGetUserById`, `makeUpdateSettingsUser`
- `makeKeyReplicacheClient`, `makeDefaultSettings`, `makeRandomId`
- `makeTemplateImage`, `makeKey`

**CRUD:**
- `createDeck`, `deleteDeck`, `deleteRemb`, `updateInfoUser`
- `generateCardsAndCreateRembs`

**Retrieval:**
- `getUserById`, `getDeckById`, `getRembById`, `getDescription`

**Computation / Transformation:**
- `computeTextModel`, `convertTool`, `toDateIso`
- `processFile`, `processCollectionAnki`
- `generateSvg`, `renderPng`

**Side effects:**
- `setDataImage`, `getDataImage`, `logHistory`

**Predicates:**
- `isGenerateCards`, `isUserAgentMobile`, `isTransactionSerializationError`

---

## One Name Per Concept

**rember project — each concept has one name across all packages:**
- "User" → `User`, `idUser`, `nameTable: "domain.user"`, prefix `"User"` — never "account"/"member"
- "Remb" → `Remb`, `idRemb`, `nameTable: "domain.remb"`, prefix `"Remb"` — never "card"/"item"
- "Deck" → `Deck`, `idDeck`, `nameTable: "domain.deck"`, prefix `"Deck"` — never "collection"/"folder"
- "Job" → `Job`, `idJob`, `nameTable: "domain.job"`, prefix `"Job"` — never "task"/"work"

**Qualified variants (same root name, different qualifier):**
- `User` → `UserMini`, `IdUser`, `ReplicacheUser`
- `Job` → `JobGenerateCards`
- `Remb` → `DraftCreateRembs`
- `DataYear` → `dataYear2024`, `dataYear2025`

---

## Nominal Consistency

**Parameter matching across call chains (rember-mcp):**
- `notes` is `notes` everywhere: tool handler param → domain function param → API call → test mock

**Parameter matching across layers (rember):**
- `idUserAuthor`: entity field → domain command arg → API handler → DB column `id_user_author`
- `tsCreated`: entity field → `tsCreated: "NOW()"` in insert → DB column `ts_created`

**Parameter matching across worker boundary (anki-wrapped):**
- `dataYear`, `dataImage`: UI caller → worker task payload → service function param — same names everywhere

**Hierarchical indexed naming (rember-mcp tests):**
- `messageModel0`, `messageModel1` — not `firstMessage`, `secondMessage`
- `inputToolCall0MessageModel0` — positional hierarchy, fully traceable
- `partText0MessageModel1` — type + index + parent chain

---

## Cross-Boundary Naming

**TypeScript → Database (rember):**

| TypeScript (camelCase) | Database (snake_case) |
|------------------------|----------------------|
| `idUser` | `id_user` |
| `idUserAuthor` | `id_user_author` |
| `tsCreated` | `ts_created` |
| `urlPicture` | `url_picture` |
| `dataStreak` | `data_streak` |
| `ixRemb` | `ix_remb` |

**TypeScript → SQL decode → TypeScript (anki-wrapped):**

| SQL column | Schema decode | TS interface field |
|------------|---------------|--------------------|
| `cards_created` | `cards_created` | `countCardsCreated` |
| `count_reviews` | `count_reviews` | `countReviews` |
| `minutes_spent_reviewing` | `minutes_spent_reviewing` | `minutesSpentReviewing` |
| `date_iso` | `date_iso` | `dateIso` |

**Internal PascalCase → MCP snake_case (rember-mcp):**
- `ToolCreateFlashcards` class → `"CreateFlashcards"` tag → `create_flashcards` MCP tool name
- Conversion: `String.pascalToSnake()` / `String.snakeToPascal()`

---

## Error Naming

Errors follow noun-first with `Error` prefix:

**rember:** `ErrorUsernameTaken`, `ErrorInputInvalid`, `ErrorFromAi`
**rember-mcp:** `ErrorApiKeyInvalid`, `ErrorReachedLimitRateLimiter`, `ErrorReachedLimitUsageTracker`, `ErrorReachedLimitQuantity`, `ErrorServerMCP`, `ErrorToolMCP`
**anki-wrapped:** `ErrorCannotUnzip`, `ErrorNotFoundCollectionApkg21b`, `ErrorCannotReadCollectionApkg21b`

---

## Layer/Service Naming

**Effect.ts layer prefix (rember-mcp):** `layerRember`, `layerTools`, `layerServerMCP`, `layerLogger`
**Effect.ts services (anki-wrapped):** `CollectionAnki`, `Persistence`, `Image` (no prefix — Effect convention)
**Replicache mutators (rember):** PascalCase verbs: `UpdateInfoUser`, `CreateDeck`, `ResetSchedulingUser`
