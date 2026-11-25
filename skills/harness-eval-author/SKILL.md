---
name: harness-eval-author
description: 'Use when authoring or validating harness-eval-protocol/v1 manifests, frozen 4-tuple arms, RFC 8785 MCP cassettes, deterministic verifiers, or vendor-blind judge rubrics. Do not use for executing campaigns (harness-eval) or querying DuckDB trace tables (harness-eval-trace).'
---

# harness-eval-author

Skill marker: `artagon-harness-eval/harness-eval-author/v1`.

Author schema-valid `harness-eval-protocol/v1` manifests (`surface: "general" | "skill_eval"`), deterministic `harness-eval-cassette/v1` fixtures, workspace verifiers, Stage-1b `trace_assertions`, and vendor-blind `judge` or per-trial recused `judge.panel` configurations that isolate one factor at a time across `claude`, `codex`, `agy`, and `copilot`. Read [protocol-schema](references/protocol-schema.md) and [cassette-and-judge](references/cassette-and-judge.md) for field-level contracts. Resolve relative links from this physical `SKILL.md`.

## Authoring workflow

1. **Define the experimental factor**: Hold three elements of the arm 4-tuple constant (`harness_config`, `mcp_servers`, `skills`, `system_prompt`) and vary only the factor under test across paired `ABBA` arms (`arms[0]` baseline vs treatment arms).
2. **Default to subscription auth**: Omit `auth_mode` or set `"auth_mode": "subscription"`. Set `"auth_mode": "api_key"` only when the user explicitly requests metered evaluation, and always pair it with finite `budget.max_cost_usd` or `budget.max_tokens` caps.
3. **Pin models explicitly**: Use exact model identifiers per harness. For Antigravity (`agy`), pin `gemini-4-carbon-high` unless the user specifies another supported `agy` model.
4. **Replace live MCP servers with cassettes**: Point `mcp_servers[].cassette_path` to a committed `harness-eval-cassette/v1` JSON file with `${TRIAL_ROOT}` and `${WS}` path placeholders and RFC 8785 canonicalized request keys. Set `"mode": "live"` only when live network variance is intentionally under test (`--allow-live-mcp`).
5. **Write deterministic verifiers first**: Prefer objective exit-code verifiers (`tasks[].verifier_cmd` or `tasks[].verifier_path`, exit `0` pass, non-zero fail) over LLM-as-judge. Add `judge` only for subjective quality dimensions.
6. **Enforce vendor-blind judging**: When `judge.enabled` is `true`, choose a cross-family `judge.harness` and `judge.model` (or per-trial recused `judge.panel`) disjoint from every evaluated arm's harness AND model vendor family (`claude` -> Anthropic, `codex` -> OpenAI, `agy` -> Google, `copilot` -> GitHub plus routed model family).
7. **Validate with `preflight`**: Run `python3 scripts/harness-eval.py --output json preflight --manifest MANIFEST --allow-host-pin` to validate against `schemas/harness-eval/protocol.schema.json` (`additionalProperties: false`).

## Validation exit codes

| Code | Meaning during authoring | Fix |
| --- | --- | --- |
| 0 | Protocol, cassettes, and judge configuration passed validation. | Proceed to `freeze` or commit the fixture. |
| 2 | JSON Schema mismatch, unknown field (`additionalProperties: false`), live MCP without `--allow-live-mcp`, or self-family judge violation. | Fix the field path named in `error` or switch to a cross-family judge. |
| 4 | `api_key` arm missing finite `max_cost_usd` / `max_tokens` or `--allow-api-keys`. | Switch arm to `"subscription"` or add finite budget caps. |
| 6 | Cassette file missing or malformed `harness-eval-cassette/v1` entry. | Regenerate or validate the cassette JSON against `cassette.schema.json`. |

## Harmless invocation

Example: `Draft a harness-eval-protocol/v1 manifest comparing baseline vs skill-enabled codex arms on a pytest fixture without running trials.`

Author or validate JSON files and run read-only `preflight` checks (`mutations="none"`). Report the skill marker `artagon-harness-eval/harness-eval-author/v1`, emit zero live model calls, and return the validated manifest path and schema check status.
