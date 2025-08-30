# v2 Parity Checklist (Feature-for-Feature with v1)

This checklist enumerates all work items required to replicate v1 functionality in a clean v2 rewrite. It is intentionally detailed and avoids code or pseudo-code. Use it to plan, implement, and verify v2.

## Architecture & Foundations
- [ ] Define top-level v2 module layout: domain, state, infrastructure (twitch, vm, storage), application (services, commands), api, cli, config.
- [ ] Establish typed configuration for: press delay, default objective, default profile, data directory, logging paths/levels, token sources.
- [ ] Configure structured logging: console and file outputs, rotation policy, log levels, module-based loggers.
- [ ] Decide async vs thread model boundaries for Twitch and VM integrations and document concurrency decisions.
- [ ] Document environment prerequisites: Python version, VirtualBox SDK, data directory location.

## Domain Models
- [ ] Profile: id, channel name, optional bot name, superusers set, users dictionary, client id, token collection (api, irc), bot id, channel id, selected challenge id, optional discord link.
- [ ] User: name, interact flag (None/True/False), interaction count, optional team, extra info (user id, superuser flag, moderator flag, following flag, total subscribed months, total cheered amount).
- [ ] Token: type (api/irc), token string, expiry timestamp, user id; operations to validate and renew tokens that mimic v1 lifecycle.
- [ ] Challenge: id, provider name (initially only virtualbox), VM name, current level integer, flags map keyed by text, hints map keyed by level, objectives map keyed by level or label, current objective reference.
- [ ] Flag: text, level integer, points value integer, optional description, optional location, captured by username or None, capture time timestamp or None.
- [ ] Hint: text, level integer, cost integer, revealed boolean, order index per level.
- [ ] Objective: objective text and optional metadata as needed by UI and messaging.
- [ ] Interaction: non-persisted interaction record fields for telemetry (viewer, action, timestamp).

## Exceptions
- [ ] Recreate custom exceptions to mirror v1 behavior and error paths: ProfileNotFoundError, ChallengeNotFoundError, NoProfileSelectedError, NoChallengeSelectedError, BoxNotInitializedError, BoxNotRunningError, BoxAlreadyRunningError, BoxNotFoundError, ProviderNotFoundError, DuplicateFlagError, FlagNotFoundError, FlagAlreadyCapturedError, ObjectiveAlreadyExists, HintNotFoundError, DuplicateHintError, HintMovementError.
- [ ] Ensure each exception is used at equivalent decision points to produce matching user-facing messages.

## Persistence Layer
- [ ] Define abstract Store interface with methods equivalent to v1 for profiles, challenges, users, and interactions.
- [ ] Implement FileStore that persists data under the default data directory (home config twitchbot) with filename conventions equivalent to v1 and auto-creation of directories.
- [ ] Implement ID allocation matching v1 semantics (next available numeric id from filenames).
- [ ] Implement save/load for profiles and challenges using a stable serialization approach and parity with v1 fields.
- [ ] Implement get/set for allowed users: return allowed usernames; set updates interact state to True and persists.
- [ ] Implement get/set for denied users: return denied usernames; set updates interact state to False and persists.
- [ ] Implement reset of interact state for provided users (remove explicit allow/deny, return to None) and persist.
- [ ] Implement no-op persistence for interactions (not saved) to match v1 behavior.
- [ ] Ensure error translation for file not found and permission errors mirrors v1 exceptions.

## State Orchestration
- [ ] Implement State lifecycle: load Store from configuration, optionally autoload default profile, and track profile, challenge, VM service, and Twitch bot references.
- [ ] Implement cleanup routine: shutdown VM if running, disconnect Twitch, save selected profile and challenge unless discard is requested.
- [ ] Implement status reporting that summarizes profile, challenge, and Twitch connection status in human-readable strings.
- [ ] Implement profile operations: create profile (with channel, optional bot, optional client id), load profile by id, save profile, verify/renew tokens on load, and handle missing or invalid profiles.
- [ ] Implement challenge operations: create, load/select by id, save changes, delete, list, and handle unknown providers.
- [ ] Implement token retrieval helpers: get api token and get irc token from the selected profile.
- [ ] Implement interaction events: stubs for new interaction, new subscription, and user cheered (telemetry hooks) consistent with v1 placeholders.
- [ ] Implement hotseat management: set hotseat to a username with optional expiry time, clear hotseat, and compute active hotseat state based on current time.
- [ ] Implement press delay override: set delay with optional expiration, compute effective delay with fallback to default.
- [ ] Implement allow_interaction check: prioritize superuser/moderator bypass; respect explicit deny; allow explicit allow; enforce freebies threshold from configuration with appropriate viewer-facing message when exceeded; increment counts as appropriate.
- [ ] Implement objective management: set objective (with duplication protection), update objective, clear objective, list objectives, and provide current objective text.

## Challenge Logic
- [ ] Implement flag creation: prevent duplicates by text; create with level and points; optionally include description and location.
- [ ] Implement flag deletion by text: error if not present.
- [ ] Implement flag retrieval: return flag object by text; error if not present.
- [ ] Implement flag listing: return flags ordered by level and presentation-friendly formatting details.
- [ ] Implement flag submission flow: validate flag text, check for duplicates, award points, mark capture time, and return status codes (does not exist, already captured, success) and points awarded.
- [ ] Implement points accounting: accumulate per-user points across captured flags; provide helper to retrieve a user’s total points in the current challenge.
- [ ] Implement hint creation: create per-level list if absent; prevent duplicates; append hint and reindex orders.
- [ ] Implement hint reordering: move up and move down operations with bounds checking and consistent reindexing; raise movement errors when invalid.
- [ ] Implement hint deletion: remove by level and index with reindexing; error when missing.
- [ ] Implement hint reveal: reveal next unrevealed hint for current level and return its text; return fallback message when none remain.
- [ ] Implement current level handling: maintain and expose the active level for hint reveal logic.

## VM Integration (VirtualBox)
- [ ] Implement VM lookup by configured name and map not found to BoxNotFoundError.
- [ ] Implement is_running check that mirrors v1’s state value interpretation.
- [ ] Implement launch: start VM process with GUI mode and wait for completion; handle already-running guard.
- [ ] Implement restore: restore to current snapshot and wait for completion.
- [ ] Implement shutdown: save state or power down based on parameter; optional restore path; handle not-running guard.
- [ ] Implement snapshot: take snapshot with timestamp-based name and include requesting username in description.
- [ ] Implement keyboard input: type text with effective press delay; sanitize text to remove unsupported characters; handle errors gracefully.
- [ ] Implement key sending: accept list of key names and modifiers; hold appropriate modifiers; press sequence; return combined list of held and pressed keys; ignore unknown keys.
- [ ] Implement release: release all held keys; guard when VM not running.
- [ ] Implement query for special keys list matching v1’s presentation.
- [ ] Ensure cleanup: on shutdown or disconnect, attempt to shutdown VM and unlock session; ignore appropriate underlying errors similar to v1.

## Twitch Integration
- [ ] Implement bot lifecycle: initialize with required tokens and channel list, start connection in background, track connection thread/state, and support clean disconnect.
- [ ] Implement event handlers parity:
  - [ ] Ready: subscribe to relevant topics and send initialization message to channel.
  - [ ] Raw PubSub: route messages by topic prefixes for channel points, bits, subscriptions, moderator actions, and whispers.
  - [ ] Channel points: parse redemption, award hotseat when requested (respect existing hotseat), reveal a hint when the Hints reward is redeemed.
  - [ ] Bits: log cheer events with username and amount.
  - [ ] Subscriptions: parse cumulative months and gift flag; thank new and returning subscribers appropriately; avoid duplicate thanks on gifted subs.
  - [ ] Moderator actions: log action, actor, and args.
  - [ ] Whispers: parse whisper content, handle flag submission workflow, private message back result, and broadcast points update in channel on success.
- [ ] Implement command error handler that intentionally ignores erroneous commands to match v1 behavior.

## Viewer Chat Commands
- [ ] help: show general usage including type, execute, press, release; include hint about mod help when caller is a mod.
- [ ] objective / obj / what: show current objective text and static rules blurb.
- [ ] source / github / gh: show repository URL.
- [ ] discord: show configured discord URL if present.

## Interaction Commands
- [ ] type: send provided text to VM; require allow_interaction; apply press delay; handle VM not running.
- [ ] execute: send provided text and a newline to VM; require allow_interaction.
- [ ] press: send special key sequence; require allow_interaction; reflect back pressed keys.
- [ ] release: release stuck modifier keys; handle VM not running gracefully.
- [ ] can_interact flow: when denied, send back specific message from allow_interaction result if present.

## Moderator Chat Commands
- [ ] help mod: display moderator-only commands.
- [ ] hotseat [username]: assign hotseat if none is active; notify on conflicts; support time-limited hotseat via channel points or command options.
- [ ] allow usernames: add usernames to allow list via state and persist through store.
- [ ] deny usernames: add usernames to deny list and persist.
- [ ] remove usernames: reset interact state to default (neither allowed nor denied) and persist.
- [ ] stop [halt] [restore]: stop VM, with halt mapping to save state or power down; optionally restore snapshot after stopping; guard when not running.
- [ ] snap: take VM snapshot; acknowledgement messaging.
- [ ] delay [ms] [seconds]: set effective press delay override and optional expiration; acknowledgement messaging.

## Interactive CLI (Admin)
- [ ] Initialize shell loop with startup banner and help.
- [ ] status: print profile, challenge, VM, and Twitch statuses.
- [ ] profile: create (prompts for channel, bot, client id), update (reserved), select by id (disallow switching after Twitch is initialized), list (reserved or implement), and display current selection.
- [ ] challenge: create (provider shown as virtualbox, prompt for VM name, optionally select), update (reserved), delete (reserved or implement), select by id, list (reserved or implement), and display current selection.
- [ ] twitch: connect services (IRC and PubSub), disconnect services, and show connection status; print current subscriptions.
- [ ] flag: create (prompts for flag text, unlock level, points, optional location, description), capture (prompts for flag and username and prints result), delete by text, list flags with formatting.
- [ ] hint: create (prompts for text and level), move up/down (prompts for level, index, direction), delete by id (prompts or parses), list per-level hints.
- [ ] objective: set current objective text, delete, list, and show.
- [ ] vm: start, stop (halt/restore options), snapshot, delay override, list special keys.
- [ ] users: allow, deny, remove (reset), list allowed, list denied; ensure persistence via store.
- [ ] hotseat: set with optional duration; clear; show current.
- [ ] tokens: show token validity and expiry, trigger renew; populate channel and bot ids.

## Security & Token Lifecycle
- [ ] Implement token validation and renewal for both api and irc tokens; on successful validation, derive and store channel id and bot id if missing.
- [ ] Ensure token strings are never logged; only metadata (expiry, user id) is logged.
- [ ] Load secrets from environment or settings; do not embed secrets in code or docs.

## Validation & Guards
- [ ] Enforce preconditions on all stateful operations (selected profile, selected challenge, running VM, Twitch connection where applicable) and produce clear error messages.
- [ ] Validate numeric inputs for level and points and handle invalid entries with friendly feedback.
- [ ] Handle missing resources gracefully and map to the appropriate custom exceptions.
- [ ] Ensure concurrency safety for VM and Twitch interactions based on chosen async/threading model.

## OBS Integration (Planned, Optional)
- [ ] Define minimal integration points to start and stop stream and switch scenes and toggle source visibility through obs-websocket 5.x.
- [ ] Make settings for OBS host, port, and password configurable and optional.
- [ ] Keep integration optional and disabled by default; document setup steps separately.

## LLM Moderator (Planned, Optional)
- [ ] Goals and scope: clarify that the LLM assists moderation by reading PubSub/chat messages and proposing or executing actions under strict rules of engagement; remains opt‑in and transparent to users.
- [ ] Event ingestion: consume chat messages, whispers, channel point redemption texts, bits/sub messages, and moderator actions from the same PubSub/event routing used by the Twitch client.
- [ ] Policy and rules of engagement: define configurable policies (toxicity, harassment, spam, hate, doxxing, adult content, malware instructions, etc.), escalation thresholds, and actions hierarchy (warn → timeout → ban) with cooldowns and rate limits.
- [ ] Prompting and guidance: design a fixed system prompt encoding channel rules, examples, and forbidden actions; parameterize with channel name, streamer preferences, and language; prohibit content generation beyond moderation judgments.
- [ ] Actions and automation: specify which actions the LLM may auto‑execute (e.g., warn) vs. require human confirmation (e.g., timeout/ban); implement a human‑in‑the‑loop queue for review.
- [ ] Safety and guardrails: enforce allowlist of permitted actions; hard caps per time window; fallback to no‑action on low confidence; require dual confirmation for severe actions; never process or store PII beyond what Twitch provides.
- [ ] Transparency and communication: craft standardized warning messages and mod‑only summaries; optionally tag messages with “[Auto‑Mod]” to distinguish LLM actions.
- [ ] Configuration: add settings for enable flag, model/provider selection, API credentials (securely), temperature/tone controls, confidence thresholds, language, and per‑rule toggles.
- [ ] Provider abstraction: define an interface for model backends to enable swapping providers or local models; include timeouts, retries, and backoff; capture token usage metrics where available.
- [ ] Privacy and data handling: document data sent to the model; allow redaction of usernames or hashes in prompts; provide configurable retention (default none) and opt‑out.
- [ ] Auditing and logging: maintain an immutable audit log of inputs, decisions, and actions with timestamps, moderator overrides, and outcomes for post‑hoc review.
- [ ] Rate limits and quotas: enforce call budgets per minute/hour and backpressure on spikes to prevent API or cost issues; degrade to rule‑based filters when over budget.
- [ ] Evaluation and tuning: define offline evaluation harness with labeled examples; track precision/recall on categories; schedule periodic calibration and drift checks.
- [ ] Failure modes and fallbacks: define behavior on provider outage/timeouts (no‑op or rule‑based); ensure the bot remains functional without LLM.

## Documentation
- [ ] Author a v2 README describing setup, dependencies, how to run, and data directory.
- [ ] Provide a command reference covering viewer, moderator, and admin CLI commands and expected outputs.
- [ ] Provide a configuration guide describing all settings and environment variables.
- [ ] Provide migration notes focused on v1 parity and validation steps.

## Testing & Verification
- [ ] Unit tests for: domain models (flags, hints, objectives), state transitions (profile/challenge selection), interaction gating and freebies, hotseat and press delay overrides with TTL, filestore read/write and id allocation, VM guards (without starting a VM), and command parsing to state action mapping.
- [ ] Integration tests with mocks for Twitch and VM to validate end-to-end flows: channel points hotseat award, hint reveal, whisper-based flag submission, moderator commands effects.
- [ ] Negative tests: attempt operations without required preconditions and verify proper errors/messages.
- [ ] Manual verification checklist: connect Twitch in a test channel, exercise all chat commands, perform VM actions, capture a flag and verify points, verify logging and persisted files.
