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

**From sim-robot (Python private field matching a local/param naming pattern used elsewhere):**
- `self._motion_axis` not `self._motion_controller` — field type is `MotionAxis | None`; matches the `motion_axis` param/local name used for this value throughout the file

**From sim-robot (Python dataclass field matching its own semantics):**
- `is_rerun_enabled` not `is_enabled` — the flag is specifically about the `rerun` logger, not a generic "enabled" state; qualify the boolean with what it's enabling

**From sim-robot (TypeScript plural type → plural constant):**
- `outputsInputNone` not `outputInputNone` — the value has type `OutputsInput` (plural), so the constant name must match the plural noun exactly

**SQL CTE names follow noun-first rule (same as Python variables):**
- `rows_step1` not `step1_rows` — noun `rows` first, qualifier `step1` last
- `rows_deck` not `deck_rows` — noun `rows` first
- `rows_step2`, `rows_coll`, `rows_step3`, `rows_window`, `rows_with_lead`, `rows_with_neighbors`, `rows_combined_with_text_prev` — consistent noun-first inside SQL string literals
- `texts_step1` not `text_step1s` (mangled plural) — noun `texts` first, qualifier `step1` last
- DuckDB `con.register("s2_observations_deck", df)` → SQL `FROM s2_observations_deck` — register name and FROM reference must match and both follow noun-first

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

**Argument name matches parameter name, even after a call-site rename (sim-robot):**
- `atomSetCommandSemantic`'s arrow-function param renamed `commandSemantic` → `commandSemanticNext` so it matches `ClientOperator.setCommandSemantic`'s own parameter name (`commandSemanticNext`) at the call site `clientOperator.setCommandSemantic(commandSemanticNext)`

**Effect value naming convention within a file (sim-robot):**
- `effectConnectOnce`, `effectRefreshLeaseAndDiscreteCommands` not `connectOnce`, `refreshLeaseAndDiscreteCommands` — parameter-less `Effect` values in the file all carry an `effect` prefix (matches `effectConnection`, `effectRefreshLeaseRepeated`)

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

---

## Physical Quantities: `<what>_<qualifier>_<unit>`

**From sim-robot.** A name for a measured quantity reads noun, then qualifier,
then unit — and the unit is always last, never split around the qualifier.

- `speed_cartesian_maximum_metres_per_second` not `speed_cartesian_metres_per_second_maximum`
- `speeds_joint_maximum_radians_per_second` not `velocities_joint_radians_per_second`
- `accelerations_joint_maximum_radians_per_second_squared`
- `acceleration_cartesian_maximum_metres_per_second_squared`
- Constants take the same shape: `SPEED_CARTESIAN_MAXIMUM_METRES_PER_SECOND`,
  `ACCELERATION_JOINT_MAXIMUM_RADIANS_PER_SECOND_SQUARED`

**The data file is the canonical spelling.** `assets/scene/limits.json` names the
cell's limits; every struct that carries those numbers (`LimitsMotion`,
`LimitsFairino`, `LimitsExecutor`) uses the file's field names verbatim, so a
number can be traced from JSON to executor by searching one string.

**Unit conversions name both units in full:**
- `convert_metres_per_second_to_millimetres_per_second` not `convert_metres_per_second_to_millimetres`
- `convert_metres_per_second_squared_to_millimetres_per_second_squared`
- `convert_metres_to_millimetres` — already symmetric, left alone

**A rate gets its own type alias, so a speed is never typed as a position:**
- `JointsRadians` (positions) beside `JointsRadiansPerSecond` (rates), both
  `tuple[float, ...] * 6`. Where a layering rule forbids importing the alias, the
  shape is spelled out again (`cell_description.limits.JointsSix`) with a comment
  on each alias pointing at the other.

---

## Wire Contracts: One Field Name Per Concept, Across Layers

**From sim-robot.** The observation stream said `positions_joint_radians`; the
request messages said `joints_target_radians`. Same concept, two spellings —
a bug. The requests moved to the observation's noun:

| old | new |
|---|---|
| `joints_target_radians` | `positions_joint_target_radians` |
| `joints_via_radians` | `positions_joint_via_radians` |

The rename crosses four boundaries mechanically and nothing else changes:

| Boundary | Form |
|---|---|
| Python struct field | `positions_joint_target_radians` |
| JSON Schema / wire JSON (msgspec `rename="camel"`) | `positionsJointTargetRadians` |
| Generated TypeScript interface | `positionsJointTargetRadians` |
| Prose in docs | "the target joints" |

**Local names near a wire field keep the local spelling.** A dataclass that only
lives inside the adapter (`MovePending.joints_target_radians`) is not the wire, so
it keeps the shorter name; only `message.positions_joint_target_radians` changes.
The local that reads the field takes the local name plus its unit:
`joints_target_radians = message.positions_joint_target_radians`.

---

## `detail` Is the Wire Word for a Reason String

**From sim-robot.** `ResultRequest.detail` is the one place a refusal, a fault or
a stop explains itself. Everything that produces one uses the same word:

- `EffectLogFault.reason` → `EffectLogFault.detail`
- `EffectEndSession.reason` → `EffectEndSession.detail`
- `find_reason_command_refused` → `find_detail_command_refused`
- `find_reason_start_refused` → `find_detail_start_refused`
- Test helper follows: `find_reasons_logged` → `find_details_logged`
- Already correct and left alone: `checks.find_detail_refusal`,
  `find_detail_joints`, `find_detail_jog_increment`

---

## Clocks: `time_now` for a Struct, `ts_now` for a Float

**From sim-robot.** `ts` is the whitelisted prefix for a *float* timestamp. A
struct carrying two clock readings is not a timestamp, so it does not get the
prefix:

- `motion_guard.guard.transition(state, input, time_now: TimeNow)` — the struct
  holds `ts_monotonic` and `ts_unix`; the parameter is `time_now`
- `script_runner.runner.build_state_script(state, ts_now: float)` — plain Unix
  seconds, so `ts_now` is right and stays
- `shell.Heartbeat.is_due(ts_now: float)` — likewise unchanged

---

## Verb Choice: `describe_*` Only for Human Text

**From sim-robot.** `describe_*` is reserved for a function whose return value is
prose a person reads. Anything returning a struct or a number gets
`compute_*` / `build_*` / `find_*`:

- `describe_step_increment(profile, motion) -> float` → `compute_step_increment`
- `describe_session_end(event) -> SessionEnd` → `build_session_end`
- Left alone, because they return `str` / `str | None` for the operator:
  `describe_session_end(event) -> str`, `describe_motion_outside_frame`,
  `describe_contact`, `_describe_holder`, `_describe_speed_above_limit`

---

## Whitelist Discipline Cuts Both Ways

**From sim-robot.** `idx` is whitelisted, `ref` is not:

- `index_joint` → `idx_joint` — `idx` is the whitelisted spelling for a
  positional index, so the spelled-out `index` is the deviation
- `resolve_reference_start` / `resolve_reference_stop` — proposed shortening to
  `resolve_ref_*` was **rejected**: `ref` is not on the whitelist
- `payload_bytes` → `bytes_payload` — `bytes` is the noun prefix for binary data,
  so it leads
- Library boundaries keep the vendor's spelling: `ref_start=` / `ref_stop=` as
  SDK keyword arguments, `GetRobotRealTimeState`, `state.jt_cur_pos`

---

## Parallel Names for Parallel Things

**From sim-robot.** Two `Heartbeat` objects in one node: the staleness clock and
the health-check publisher. `node_script` already called them `heartbeat_tick`
and `heartbeat`; `node_motion_guard` called the first one `tick`. Renaming
`tick` → `heartbeat_tick` makes the two nodes read identically.

The check before renaming: **a name bound to an external id must match that id.**
`tick` would have had to stay if `dataflows/sim.yml` declared a `tick` input on
the guard — it declares none, so the Python name is free.

**A struct field gains the qualifier its counterpart already carries:**
`SampleFeed.velocity_linear_metres_per_second` →
`velocity_tool_center_point_linear_metres_per_second`, matching
`StateRobot.velocity_tool_center_point_linear_metres_per_second`, so the
assignment from adapter to wire message is field-for-field with one name.

---

## A Local Name Can Outrank the Wire Name It Was Copied From

**From sim-robot.** The concept was already `number_output` / `number_input` on
`script_language.program.SetOutput` / `WaitInput` — a line references a digital
port by the number printed on the control box. The wire structs that carry the
same value to a robot node had drifted to `IndexOutputDigital` /
`IndexInputDigital` (type aliases) and `RequestSetOutput.index_output` /
`RequestReadInput.index_input` (fields), a different root noun for the same
concept. Fixed by renaming the wire side to match the program side, not the
other way around, because `number_output` was already the name a person reads
on the pendant screen; `index` would have implied 0-based array indexing,
which is not what the value means:

| old | new |
|---|---|
| `IndexOutputDigital` | `NumberOutputDigital` |
| `IndexInputDigital` | `NumberInputDigital` |
| `RequestSetOutput.index_output` | `RequestSetOutput.number_output` |
| `RequestReadInput.index_input` | `RequestReadInput.number_input` |

Crossed boundaries mechanically: JSON wire key `indexOutput`/`indexInput` →
`numberOutput`/`numberInput` in test fixtures; every call site that built or
read the request (`3_runner/tick.py`, `3_robot_mujoco/robot_simulated.py`,
`3_robot_fairino_sdk/robot_fairino.py`) followed. The vendor SDK calls the
renamed fields feed (`sdk.SetDO(message.number_output, ...)`,
`sdk.GetDI(message.number_input)`) keep the SDK's own argument names
unchanged — only the message field changed, not the library boundary.

---

## `has_` Is Not a Boolean Prefix Here — `is_` Is

**From sim-robot.** `StateRunner.has_changes_unsaved` was the one boolean in
the codebase spelled with `has_` instead of `is_`. Renamed to
`is_program_unsaved` — note the noun also changed from `changes` to `program`
so the name reads as "is the program unsaved" rather than "has unsaved
changes", matching the `is_` + adjective shape every other boolean in the
codebase uses (`is_suspended`, `is_first_review`, `isInferenceRunning`).
Followed through the generated-types boundary mechanically:
`is_program_unsaved` (Python struct field) → msgspec `rename="camel"` →
`isProgramUnsaved` (wire JSON and generated TypeScript interface) →
`isProgramUnsaved` (every React prop, state read, and test fixture in
`app-operator`).

---

## Vendor Numbering Gets a Word, Not an Abbreviation — `ref` → `reference`

**From sim-robot.** `jog.py` names constants after the vendor SDK's own `ref`
argument to `StartJOG`/`StopJOG`. `ref` is not on the whitelist (unlike `idx`),
so the constants spell it out even though the SDK keyword argument they feed
stays `ref=` at the call site:

- `REF_START_FRAME_JOINT` → `REFERENCE_START_FRAME_JOINT` (and five siblings:
  `_BASE`, `_TOOL`, `REF_STOP_FRAME_*`)
- `AXIS_UNIT_BY_NAME` → `UNIT_AXIS_BY_NAME` — noun `unit` first, `axis` is the
  qualifier (a dict of per-axis unit vectors, not a dict of axes)
- `percentage_velocity` → `speed_percentage` — noun `speed` first; `velocity`
  was a synonym for the same value the SDK calls `vel`, a second name for one
  concept
- `PERCENTAGE_ACCELERATION_JOG` → `ACCELERATION_JOG_PERCENTAGE` — unit-like
  qualifier (`PERCENTAGE`) moves last, matching the `<what>_<qualifier>_<unit>`
  shape used for physical quantities elsewhere in this file

**Test constants follow the same noun-first correction (`3_robot_fairino_sdk`,
`4_dora_nodes`):** `PERCENTAGE_SPEED_JOINT` → `SPEED_JOINT_PERCENTAGE`;
`DEGREES_JOINT_LIMIT` → `LIMIT_JOINT_DEGREES`; `RADIANS_JOINT_LIMIT` →
`LIMIT_JOINT_RADIANS` (renamed independently in two test files that each
define their own copy of the constant — same name, no shared import).

**A test helper that returns a value, named as a bare noun, gets a verb:**
`arguments_start_jog()` → `get_arguments_start_jog()` (returns the arguments
of the one `StartJOG` call made); `change_reference_maximum_per_step()` →
`compute_change_reference_maximum_per_step()` (derives a bound from limits,
so `compute_` rather than `get_`).

**A cross-package function name carried a wrong noun:** `get_limits_velocity_joint`
(in `cell_description.manifests`) named its return value `velocity` where every
caller and sibling constant calls the same quantity `speed`
(`speeds_joint_maximum_radians_per_second`, `SPEED_JOINT_PERCENTAGE`). Renamed
to `get_limits_speed_joint` and followed into every caller across package
boundaries (`cell_model`, `robot_mujoco` tests) — the function's own
`limit_velocity_radians_per_second` manifest key it reads was left alone
because it wasn't part of the requested rename.

**Test-harness builder methods take a `build_` verb to match their sibling
`build_point`/`build_limits_program`:** a `Harness` class had accreted plain-noun
methods that each construct one item (`state_robot`, `command_jog`, `jog_joint`,
`jog_cartesian`, `jog_ready`, `jog_released`, `connection`, `result`,
`result_check`, `command`) → `build_state_robot`, `build_command_jog`,
`build_jog_joint`, `build_jog_cartesian`, `build_jog_ready`,
`build_jog_released`, `build_connection`, `build_result`, `build_result_check`,
`build_command`. The rename is call-site-only: a mechanical find-and-replace
on the bare noun also touched unrelated dataclass fields that happen to share
the same word (`ItemStateRobot.state_robot`, `ItemCommandJog.command_jog`,
`ItemCommandScript.command`, `EffectSendResultRequest.result`,
`EffectSendResultScript.result`) and one docstring's prose ("the command, then
the file's answer") — none of those are the harness method being renamed, so
they were reverted to their original spelling.
