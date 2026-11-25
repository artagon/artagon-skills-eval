# Capability: harness-eval-runtime

## ADDED Requirements

### Requirement: Modular Four-CLI Transcript Decoders and Four-Layer Fusion
`artagon_eval_core.shell.transcript` SHALL split decoding into per-CLI modules (`claude`, `codex`, `agy`, `copilot`), `otel_reducer`, and 4-layer `fusion` producing frozen `TrialTrace` records with derived `hook_lifecycle`/`subagent` spans, normalized `hook_events`, and pre-serialization secret/PII redaction. Each module SHALL stay within `<= 300` LOC and `CC <= 8` (CI cap `<= 10`).

#### Scenario: Fusing multi-layer evidence into a frozen TrialTrace
- GIVEN transcript events, OTLP spans, lifecycle/subagent hook events, and workspace diffs from a trial run
- WHEN `fusion` merges the four layers through `SecretScrubberPort`
- THEN it SHALL return `Ok(TrialTrace)` with derived `hook_lifecycle`/`subagent` spans, scrubbed `hook_events`, redacted `RedactedStr` outputs, and immutable tuple/map collections.

### Requirement: Isolated Execution Shell, Custody, Multiplexers, and Cassette Replay
`artagon_eval_core.shell` SHALL implement isolated trial workspaces (`/var/tmp/art-eval-<uid>/` `0700`), `flock`-guarded holdout ledgers (`<= 3` evaluation cap), `0600` HMAC keys, read-only method-only keyring access, RFC 8785 stdio MCP cassette replay/record, loopback OTLP collection, vendor-blind judge panels, and multiplexer drivers (`ntm`, `herdr`, `cao`, `hcom`).

#### Scenario: Refusing holdout evaluation past the ledger cap
- GIVEN a campaign whose `flock`-protected `holdout_ledger.json` already records 3 holdout evaluations
- WHEN a fourth holdout evaluation is requested
- THEN the custody port SHALL fail closed with `Error(IsolationTamperError)` (`exit 5`) without launching any trial.

### Requirement: macOS Fail-Closed Subscription Auth and PII Redaction
`artagon_eval_core.shell` and `runtime.redact` SHALL enforce macOS fail-closed subscription auth (`claude`, `copilot` with `COPILOT_EVAL_GITHUB_TOKEN`, `agy`) and scrub secrets and PII keys/emails before persisting traces, `hook_events`, or holdout-hashed exports.

#### Scenario: Failing closed on macOS subscription auth gaps and scrubbing hook PII
- GIVEN a macOS host lacking isolated subscription credentials for `claude`, `copilot`, or `agy`, or a hook payload containing PII email/account fields
- WHEN preflight checks run or `SecretVault` scrubs hook payloads prior to JSON serialization
- THEN preflight SHALL return `Error(CredentialUnavailableError)` (`exit 3`) and `SecretVault` SHALL redact PII/secret values idempotently while preserving safe git SSH remotes.

### Requirement: Read-Only DuckDB Trace Store and OTLP Export
`artagon_eval_core.store` SHALL separate pre-redacted 6-table Parquet compaction (`trials`, `spans`, `tool_calls`, `mcp_calls`, `file_diffs`, `hook_events` in `parquet_writer`), read-only DuckDB querying with holdout split guards (`duckdb_query`), SQL read-only enforcement (`sql_guard`), and loopback-guarded OTLP JSON/Protobuf export with root-span `Span.Event` hook telemetry (`otlp_export`).

#### Scenario: Rejecting mutating SQL or holdout leakage in trace-query and OTLP export
- GIVEN a read-only 6-table DuckDB trace store containing train, val, and quarantined test splits with `hook_events`
- WHEN a caller submits a `DROP`/`ATTACH`/`COPY` statement or exports holdout traces without `--hash-holdout-payloads`
- THEN `sql_guard`, `duckdb_query`, or `otlp_export` SHALL reject the operation with a typed `EvalError`, modify zero database state, and hash `hook_events` and root-span `Span.Event` `hook.payload` when holdout hashing is enabled.

### Requirement: ADR-0012 Hot-Path Shim Isolation and Latency Budget
`artagon_eval_core.shims` (`wire`, `scrub`, `trampoline`, `hook_sink`) SHALL run under `python -P -s -m` importing only the Python standard library and optional `msgspec`, enforced by `import-linter`, with hot-path invocation overhead `<= 5ms`.

#### Scenario: Hot-path shim imports zero heavy runtime libraries
- GIVEN a fresh Python subprocess invoked with `-P -s -m artagon_eval_core.shims.wire`
- WHEN the module initializes and processes a framed message
- THEN `sys.modules` SHALL contain zero heavy dependencies (`pydantic`, `expression`, `duckdb`, `typer`, `structlog`, `detect_secrets`).

### Requirement: Unified `harness-eval` CLI, Bootstrap Launchers, and External Repo Overlays
`artagon_eval_core.cli` SHALL inject `AppContext` via Typer `ctx.obj` (zero module globals), emit `harness-eval-envelope/v1` on `stdout`, log redacted `EvalError` records to `stderr`, and support `--repo-root` / `--config-dir` 4-layer immutable config overlays over packaged defaults with zero hardcoded `artagon-scripts` paths. Stdlib `scripts/harness-eval*.py` launchers SHALL stay Python 3.9 AST-parseable with verified billing-var parity.

#### Scenario: Targeting an external Agent Skill repository with zero config files
- GIVEN a synthetic external repository containing `skills/<name>/SKILL.md` and no `configs/` directory
- WHEN `harness-eval --repo-root <path> preflight` or `freeze` runs
- THEN packaged Layer-1 defaults SHALL load cleanly via `importlib.resources` and never reference sibling repo paths.
