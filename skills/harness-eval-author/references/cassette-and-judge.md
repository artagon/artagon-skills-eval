# MCP Cassette and Blind Judge Reference (`harness-eval-author`)

## Deterministic `harness-eval-cassette/v1` Format

`src/artagon_harness_eval/cassette.py` replays stdio Model Context Protocol (MCP) traffic (`2026-07-28` and legacy `2024-11-05` `initialize` negotiation) without external network calls:

1. **Path Normalization**: Before computing `normalized_jcs_sha256`, `cassette.py` replaces the physical workspace path with `${WS}` and the trial root with `${TRIAL_ROOT}`.
2. **RFC 8785 Canonicalization (JCS)**: JSON-RPC `method`, `tool_name`, and normalized `params` are canonicalized with sorted UTF-16 key ordering and compact separators, then hashed with SHA-256 (`exact_jcs_sha256` and `normalized_jcs_sha256`).
3. **FIFO Queues**: Repeated identical tool calls pop responses in First-In First-Out (`FIFO`) order from `responses[]` (falling back to `default_response` when provided) so stateful read-modify-read sequences replay deterministically.
4. **Miss Accounting**: Unmatched `tools/call` requests return a structured JSON-RPC error (`cassette_miss`) and append a record to `<trial>/trace/mcp_calls.jsonl` so `ITT` sensitivity analysis separates fixture gaps from model errors.

```json
{
  "schema_version": "harness-eval-cassette/v1",
  "server_name": "canary-docs",
  "protocol_version": "2026-07-28",
  "server_version": "1.0.0",
  "tools": [
    {
      "name": "lookup_doc",
      "description": "Look up fixture documentation by topic.",
      "inputSchema": {
        "type": "object",
        "properties": {"topic": {"type": "string"}},
        "required": ["topic"]
      }
    }
  ],
  "interactions": [
    {
      "method": "tools/call",
      "tool_name": "lookup_doc",
      "match_keys": {"topic": "retry"},
      "responses": [
        {
          "result": {
            "content": [{"type": "text", "text": "Use exponential backoff with jitter."}],
            "isError": false
          }
        }
      ]
    }
  ]
}
```

## Vendor-Blind and Billing-Blind Judge Rules

- **Clean Diff Extraction**: `src/artagon_harness_eval/judge.py` builds a temporary `GIT_INDEX_FILE` excluding harness artifacts (`.claude`, `.codex`, `.gemini`, `.copilot`, `.kimi`, `.ntm`, `.herdr`, `trace/`) so only workspace deliverables reach the judge.
- **Token Scrubbing**: Harness signatures, model names, billing strings, API-key prefixes, and trial IDs are scrubbed unless already present in the baseline fixture (`baseline_text` awareness).
- **Canary Enforcement**: Every trial plants a unique canary token inside trial metadata; if the canary appears anywhere in the sanitized judge prompt, scoring aborts with exit `5` (`EXIT_ISOLATION_CANARY`).
- **Family Separation**: `judge.harness` and `judge.model` vendor family cannot overlap any evaluated arm (`claude` -> Anthropic, `codex` -> OpenAI, `agy` -> Google, `copilot` -> GitHub plus routed model family, `kimi` -> Moonshot). Multi-family candidate arms must select a judge whose vendor family is disjoint from every candidate arm (or a `>= 3`-family `judge.panel` with per-trial vendor recusal).
