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
- Paths: `path_dataset`, `path_output`, `path_parquet`, `path_model`, `path_log`, `path_difficulty`, `path_map_user`, `path_map_card`, `path_train`, `path_validation`, `path_test`, `path_embeddings`, `path_checkpoint`, `path_mapping_card`, `path_mapping_user`, `path_features`, `path_predictions_intra_day`, `path_predictions_between_days`
- Directories: `dir_daily`, `dir_data`, `dir_results`
- DataFrames: `df_reviews`, `df_cards`, `df_retention`, `df_feat`, `df_ret`, `df_log`, `df_features`
- Dicts: `dict_review`, `dict_card_to_idx`, `dict_idx_to_card`, `dict_ts_to_row`
- Arrays: `array_feats`, `array_ret`, `arr_acc_card`
- Counts: `cnt_train`, `cnt_validation`, `cnt_test`, `cnt_samples`, `cnt_correct`, `cnt_batch`
- Indices: `idx_row`, `idx_batch_start`, `idx_card_ret`, `idx_card_arr`, `idx_card_target`, `idx_card_val`, `indices_row`, `indices_retrieval`
- Dimensions: `dim_input`, `dim_embed`, `dim_slot`
- Means/stats: `mean_feature`, `std_feature`, `var_feature`, `mean_pop_train`, `sums_feature`, `sums_sq_feature`
- Embeddings: `embeddings_card`, `embeds_user`, `embeds_ret`
- Masks: `mask_nan_4`, `mask_padding`
- Sets: `set_users`, `set_ts`
- Files: `files_between_days`
- Mappings: `map_user`, `mapping_card`
- Permutations: `perm_user`
- Accumulated lists: `probs_all_intra_day`, `probs_all_between_days`, `probs_list_validation`, `labels_list_validation`
- Accumulated scalars: `loss_total`, `loss_total_validation`, `cnt_correct_validation`, `cnt_validation`
- Per-epoch metrics: `loss_train`, `acc_train`, `loss_validation`, `acc_validation`, `auc_validation`
- Intervals: `interval_days`, `interval_ms`
- Durations: `duration_ms_total` not `duration_total_ms` — noun `duration_ms` first, qualifier `total` last
- Booleans: `is_suspended`, `is_first_review`
- Masks: `mask_pre_cutoff` not `ixs_before_cutoff` — noun `mask` for boolean arrays; `ixs` prefix reserved for fractional/sort indices

**Snakemake param keys (same noun-first rule applies):**
- `dir_daily` not `daily_dir` — directory of per-user daily parquets
- `dir_data` not `data_dir` — directory of analysis-internal data files
- `dir_results` not `results_dir` — directory of analysis results
- `path_output` not `output_path` — output file path (when assigned from `snakemake.output.*`)

**ML model constant naming:**
- `FEATURE_COLS_USER` not `USER_FEATURE_COLS` — qualifier after noun
- `COLS_POST_REVIEW` not `POST_REVIEW_COLS` — qualifier after noun

**ML function naming (verb-first, then result-type noun, then qualifiers):**
- `get_df_feature_user` not `get_user_feature_df` — verb `get` + result type `df` + qualifiers
- `get_set_timestamp_ms_user` not `get_user_timestamp_ms_set` — verb `get` + result type `set` + qualifiers

**Class constructor parameter naming:**
- `path_checkpoint` not `checkpoint_path` — noun `path` first
- `path_embeddings` not `embeddings_path` — noun `path` first
- `path_mapping_card` not `card_mapping_path` — noun `path` first

**Class instance attribute naming (private):**
- `_embeddings_card` not `_card_embeddings`
- `_dim_embed` not `_embed_dim`
- `_mean_feature`, `_std_feature` not `_feature_mean`, `_feature_std`
- `_mean_pop_train` not `_train_pop_mean`
- `_stats_card` not `_card_stats`
- `_cache_user` not `_user_cache`
- `_dict_card_to_idx` not `_card_to_idx` — dict prefix required for mapping types
- `_dict_idx_to_card` not `_idx_to_card` — dict prefix required for mapping types

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
