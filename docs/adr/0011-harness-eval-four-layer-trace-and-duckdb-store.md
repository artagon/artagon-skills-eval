---
status: accepted
date: 2026-11-14
decision-makers: []
consulted: []
informed: []
---

# ADR-0011: Fuse four-layer harness traces into pre-redacted Parquet and read-only DuckDB

## Status

Accepted.

## Context

No single telemetry channel captures complete, tamper-evident behavior across
`claude`, `codex`, `agy`, and `copilot`: hooks provide exact deterministic tool
boundaries (and Codex injects hook `stdout` into prompt context), OpenTelemetry
provides GenAI token/TTFT spans for `claude`, `codex`, and `copilot` (while `agy`
records internal reasoning in `transcript_full.jsonl`), and shell commands can
mutate files outside structured edit tools. Running heavy Java/Docker observability
servers during trials adds latency and failure modes.

## Decision

1. Collect four complementary local layers per trial:
   - Layer 1: Zero-output command hooks (`harness_eval_hook_sink.py`) over an
     out-of-workspace `0600` Unix socket (`/tmp/art-htrc-<rand>/sock`) with
     per-trial HMAC `O_APPEND` fallback and `<= 5s` `exit 0` budget.
   - Layer 2: Loopback `127.0.0.1:0` bearer-authenticated OTLP/HTTP JSON+protobuf
     collector (`harness_eval_otlp_sink.py`) plus Copilot JSONL file ingestion.
   - Layer 3: Native CLI session transcripts (`stream-json`, `rollout-*.jsonl`,
     `transcript_full.jsonl`, Copilot JSON).
   - Layer 4: Supervisor ground truth (`shim-exec.json`, `child-execs.jsonl`,
     `mcp_calls.jsonl`, and pre/post workspace SHA-256 tree diffs).
2. Run a pre-write secret redactor in `harness_eval_trace.py` before writing any
   normalized JSONL or Parquet file.
3. Compact campaign traces into `{trials,spans,tool_calls,mcp_calls,file_diffs}.parquet`
   queried via read-only DuckDB (`access_mode='READ_ONLY'`,
   `enable_external_access=false`), and provide optional post-run exporters to
   `otlp-json`, Arize Phoenix (`127.0.0.1:6006`), and MLflow 3.

## Alternatives considered

- Chosen: lightweight stdlib socket/HTTP collection during trials + Parquet/DuckDB
  analytics + optional post-run Phoenix/MLflow export.
- Rejected: mandatory live Phoenix or MLflow servers during trial execution.
- Rejected: hook-only or transcript-only collection, which misses either token/TTFT
  metrics or `Bash` side effects and MCP wire payloads.

## Consequences

Trials incur near-zero collection overhead and zero prompt perturbation, while
operators gain full SQL analytics offline and one-command export to open-source
trace UIs.

## Links to OpenSpec change

- `@change:add-subscription-harness-eval`
- `openspec/changes/add-subscription-harness-eval/proposal.md`
- `openspec/changes/add-subscription-harness-eval/design.md`
- `openspec/changes/add-subscription-harness-eval/tasks.md`

## Links to affected requirements

- `@spec:harness-trace-collection#zero-perturbation-hook-collection-over-out-of-workspace-socket`
- `@spec:harness-trace-collection#local-loopback-opentelemetry-genai-ingestion`
- `@spec:harness-trace-collection#pre-write-secret-redaction-and-four-layer-parquetduckdb-store`

## Links to tests and evidence

Verified by `tests/test_harness_eval_hook_and_otlp_sinks.py`,
`tests/test_harness_eval_trace_properties.py`, and
`tests/test_harness_eval_store_duckdb.py`.

## Supersedes / superseded by

- Supersedes: N/A
- Superseded by: N/A
