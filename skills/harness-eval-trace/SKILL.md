---
name: harness-eval-trace
description: 'Use when querying 4-layer harness evaluation traces with read-only DuckDB SQL or exporting trial spans to OTLP JSON, Arize Phoenix, or MLflow 3 via harness-eval.py. Do not use for running campaigns (harness-eval) or authoring protocol manifests (harness-eval-author).'
---

# harness-eval-trace

Skill marker: `artagon-harness-eval/harness-eval-trace/v1`.

Query compacted 4-layer evaluation telemetry (`trials`, `spans`, `tool_calls`, `mcp_calls`, `file_diffs`, and `hook_events`) through read-only DuckDB SQL (`SQLite` fallback in bare-host mode) and export redacted OpenTelemetry (`OTel`) GenAI waterfalls (including root-span `Span.Event` hook telemetry) across `otlp-json`, `phoenix` (`application/x-protobuf` `bytes.fromhex()` 16/8-byte IDs + OpenInference `0.1.46` skill metadata), `mlflow` (`/v1/traces` + `--mlflow-experiment-id`), `langfuse-otlp`, and `waza-outcome` (with `--hash-holdout-payloads` HMAC hashing for `test` / unsplit `v1`). Read [table-schemas](references/table-schemas.md) and [sql-and-export-recipes](references/sql-and-export-recipes.md) for column definitions and ready-to-run queries. Resolve relative links from this physical `SKILL.md`.

## Four-layer trace fusion

`artagon_harness_eval.transcript` and `artagon_harness_eval.store` fuse four independent layers per trial after pre-write secret redaction:

1. **Layer 1 — Zero-perturbation Unix-socket hooks**: `artagon_harness_eval.shims.hook_sink` timestamps tool (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`), lifecycle (`SessionStart`/`SessionEnd`, `PreInvocation`/`PostInvocation`, `PreCompact`/`PostCompact`, `PermissionRequest`/`PermissionResult`/`PermissionDenied`, `PreModelRequest`/`PostModelRequest`), subagent (`SubagentStart`/`SubagentStop`), and point-in-time (`UserPromptSubmit`, `InstructionsLoaded`, `FileChanged`, `Notification`, `Stop`, `StopFailure`, `Interrupt`) events with monotonic nanoseconds over `/tmp/art-htrc-<rand>/sock`.
2. **Layer 2 — Local OTLP GenAI spans**: Loopback OTLP/HTTP collector (`claude`, `codex`) and direct JSONL file exporter (`copilot` `COPILOT_OTEL_FILE_EXPORTER_PATH`) capture `invoke_agent`, `chat`, `execute_tool`, Time To First Token (`TTFT`), and cache/reasoning token counts.
3. **Layer 3 — Native transcripts**: Harness session logs (`claude` `stream-json`, `codex` `rollout-*.jsonl`, `agy` `transcript_full.jsonl` via the 6-site `1.5.9` parser, and `copilot` JSON).
4. **Layer 4 — Supervisor ground truth**: Single-exec `shim-exec.json`, deterministic `mcp_calls.jsonl` (including `cassette_miss` flags), and pre/post workspace SHA-256 `file_diffs` that catch `Bash` file edits invisible to file-tool hooks.

## Read-only query and export commands

1. **Run a read-only SQL query**:
   `python3 scripts/harness-eval.py --output json trace-query --campaign CAMPAIGN_DIR --sql "SELECT arm_id, COUNT(*) AS n, AVG(CASE WHEN verified_success THEN 1.0 ELSE 0.0 END) AS itt_pass_rate FROM trials GROUP BY arm_id ORDER BY arm_id"`
2. **Export OTLP JSON spans to disk**:
   `python3 scripts/harness-eval.py --output json trace-export --campaign CAMPAIGN_DIR --format otlp-json --out CAMPAIGN_DIR/exports/otlp-traces.json`
3. **Export spans to local Arize Phoenix (`http://127.0.0.1:6006/v1/traces`) or MLflow 3**:
   `python3 scripts/harness-eval.py --output json trace-export --campaign CAMPAIGN_DIR --format phoenix --out CAMPAIGN_DIR/exports/phoenix.json [--endpoint http://127.0.0.1:6006/v1/traces]`

## Guardrails and exit codes

- `trace-query` opens DuckDB with `access_mode='READ_ONLY'` and `enable_external_access=false` (or SQLite `?mode=ro`) and accepts only a single `SELECT` or `WITH` statement. DDL, DML, `COPY`, `ATTACH`, `INSTALL`, `LOAD`, `PRAGMA`, and file-reading table functions (`read_parquet(...)`, `read_csv(...)`) fail closed with exit `2`.
- Network export (`--endpoint`) allows loopback endpoints (`127.0.0.1`, `localhost`, `[::1]`) by default so redacted traces never leave the machine accidentally.

| Code | Meaning | Action |
| --- | --- | --- |
| 0 | Query or export completed; rows or export receipt returned in `data`. | Summarize findings for the user. |
| 2 | Rejected mutating/external SQL statement, missing campaign store, or non-loopback export endpoint. | Rewrite SQL as a pure `SELECT`/`WITH` over the 6 registered views (`trials`, `spans`, `tool_calls`, `mcp_calls`, `file_diffs`, `hook_events`). |

## Harmless invocation

Example: `Show a read-only SQL query comparing tool failure rates and cassette misses by arm for /tmp/campaign-01.`

Run read-only `trace-query` (`mutations="none"`) or return SQL recipes when no campaign directory exists yet. Report the skill marker `artagon-harness-eval/harness-eval-trace/v1` and never mutate campaign artifacts.
