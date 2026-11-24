# Trace Store Table Schemas (`harness-eval-trace`)

Each campaign compacts redacted per-trial traces into `<campaign>/tables/*.parquet` (queried via DuckDB views) and mirrors them into `<campaign>/tables/store.sqlite` for bare-host fallback.

## 1. `trials`

| Column | Type | Description |
| --- | --- | --- |
| `trial_id` | `TEXT` | Unique trial identifier. |
| `campaign_id` | `TEXT` | Campaign identifier. |
| `arm_id` | `TEXT` | Arm identifier from protocol. |
| `task_id` | `TEXT` | Task identifier from protocol. |
| `block_id` | `TEXT` | Paired `ABBA` block identifier. |
| `harness` | `TEXT` | `claude`, `codex`, `agy`, `copilot`, or `kimi`. |
| `model` | `TEXT` | Requested model identifier. |
| `observed_model` | `TEXT` | Model reported in transcript or OTel span. |
| `auth_mode` | `TEXT` | `subscription` or `api_key`. |
| `execution_mode` | `TEXT` | `headless`, `ntm`, `herdr`, or `cao`. |
| `status` | `TEXT` | `completed`, `failed`, `timeout`, `quota_censored`, `billing_violation`, `isolation_failed`, `cassette_miss_failed`, or `multiplexer_failed`. |
| `exit_code` | `BIGINT` | Process exit status. |
| `verified_success` | `BOOLEAN` | `true` when deterministic verifier passed. |
| `judge_score` | `DOUBLE` | Optional blind-judge score (`0.0`..`1.0`). |
| `redaction_applied` | `BOOLEAN` | Whether pre-write redaction scrubbed one or more secrets. |
| `redacted_count` | `BIGINT` | Number of secret substrings redacted pre-write. |
| `duration_ms` | `DOUBLE` | End-to-end wall-clock duration in milliseconds. |
| `input_tokens` | `BIGINT` | Total input tokens. |
| `output_tokens` | `BIGINT` | Total output tokens. |
| `cache_read_tokens` | `BIGINT` | Cache-read input tokens. |
| `reasoning_tokens` | `BIGINT` | Reasoning/thinking tokens. |
| `cost_usd` | `DOUBLE` | Reported cost in USD (when `auth_mode == 'api_key'`). |
| `ttft_ms` | `DOUBLE` | Time To First Token in milliseconds. |
| `tool_call_count` | `BIGINT` | Fused tool call count. |
| `mcp_call_count` | `BIGINT` | Total MCP calls recorded. |
| `mcp_cassette_miss_count` | `BIGINT` | Unmatched `mcp_cassette` requests. |
| `file_diff_count` | `BIGINT` | Changed workspace files between pre/post tree snapshots. |
| `hook_event_count` | `BIGINT` | Layer 1 hook events captured. |
| `otel_span_count` | `BIGINT` | Layer 2 OTel spans captured. |

## 2. `spans`

| Column | Type | Description |
| --- | --- | --- |
| `trial_id` | `TEXT` | Parent trial ID. |
| `trace_id` | `TEXT` | Trace identifier. |
| `span_id` | `TEXT` | Span identifier. |
| `parent_span_id` | `TEXT` | Parent span identifier. |
| `span_kind` | `TEXT` | `invoke_agent`, `chat`, `execute_tool`, `subagent`, `mcp_rpc`, `hook_lifecycle`, or `supervisor`. |
| `name` | `TEXT` | Operation or tool name. |
| `source_layer` | `TEXT` | `hook`, `otel`, `transcript`, `supervisor`, or `fused`. |
| `start_wall_ns` | `BIGINT` | Start timestamp in nanoseconds. |
| `end_wall_ns` | `BIGINT` | End timestamp in nanoseconds. |
| `duration_ms` | `DOUBLE` | Span duration in milliseconds. |
| `ttft_ms` | `DOUBLE` | Time To First Token in milliseconds. |
| `status` | `TEXT` | `ok` or `error`. |
| `tool_name` | `TEXT` | Tool name for `execute_tool` spans. |
| `tool_use_id` | `TEXT` | Correlated call ID. |
| `attributes_json` | `TEXT` | Redacted JSON attributes (`gen_ai.*`, exit codes). |

## 3. `tool_calls`

| Column | Type | Description |
| --- | --- | --- |
| `trial_id` | `TEXT` | Parent trial ID. |
| `call_index` | `BIGINT` | 0-based ordinal within the trial. |
| `tool_use_id` | `TEXT` | Correlated hook/OTel/transcript call ID. |
| `tool_name` | `TEXT` | Normalized tool name (`Bash`, `Read`, `Edit`, `mcp__*`, etc.). |
| `source_layer` | `TEXT` | Confirming layer (`hook`, `otel`, `transcript`, or `fused` when 2+ layers agree). |
| `duration_ms` | `DOUBLE` | Execution latency in milliseconds. |
| `status` | `TEXT` | `ok`, `error`, or `unknown`. |
| `arguments_json` | `TEXT` | Redacted tool input JSON. |
| `result_summary` | `TEXT` | Redacted tool result summary. |

## 4. `mcp_calls`

| Column | Type | Description |
| --- | --- | --- |
| `trial_id` | `TEXT` | Parent trial ID. |
| `server_name` | `TEXT` | Configured MCP server name. |
| `seq` | `BIGINT` | Monotonic call sequence number. |
| `method` | `TEXT` | JSON-RPC method (`initialize`, `tools/list`, `tools/call`). |
| `tool_name` | `TEXT` | MCP tool name for `tools/call`. |
| `exact_jcs_sha256` | `TEXT` | Exact RFC 8785 JCS SHA-256 digest. |
| `normalized_jcs_sha256` | `TEXT` | Workspace-normalized RFC 8785 JCS SHA-256 digest. |
| `match_tier` | `TEXT` | `exact`, `normalized`, `match_keys`, `default_response`, `protocol`, or `miss`. |
| `cassette_miss` | `BOOLEAN` | `true` on replay miss, `false` on hit. |
| `is_error` | `BOOLEAN` | Whether the MCP response was an error. |
| `duration_ms` | `DOUBLE` | Replay or live response latency in milliseconds. |

## 5. `file_diffs`

| Column | Type | Description |
| --- | --- | --- |
| `trial_id` | `TEXT` | Parent trial ID. |
| `rel_path` | `TEXT` | Workspace-relative POSIX file path. |
| `change_kind` | `TEXT` | `added`, `modified`, or `deleted`. |
| `before_sha256` | `TEXT` | Pre-trial SHA-256 digest (`NULL` if added). |
| `after_sha256` | `TEXT` | Post-trial SHA-256 digest (`NULL` if deleted). |
| `before_size` | `BIGINT` | File byte length before trial (`NULL` if added). |
| `after_size` | `BIGINT` | File byte length after trial (`NULL` if deleted). |
