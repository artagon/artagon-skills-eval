---
name: harness-eval
description: 'Use when running, previewing, freezing, importing Waza suites, optimizing candidates with GEPA, checking auth or Nix closures, or analyzing multi-CLI harness evaluation campaigns with harness-eval.py across Claude, Codex, Antigravity, Copilot, or Kimi. Do not use for authoring protocol manifests or MCP cassettes (harness-eval-author), querying DuckDB traces or exporting OTel spans (harness-eval-trace), or general swarm operations (art-swarm).'
---

# harness-eval

Skill marker: `artagon-harness-eval/harness-eval/v1`.

Operate `harness-eval.py` to validate credentials, freeze reproducible `harness-eval-protocol/v1` manifests, preview paired `ABBA` schedules, execute multi-CLI trials, and compute Intention-To-Treat (`ITT`) lift with paired bootstrap `95%` confidence intervals and Holm-Bonferroni multiplicity correction. Read [cli-workflow](references/cli-workflow.md) and [safety-and-auth](references/safety-and-auth.md) as needed. Resolve relative links from this physical `SKILL.md`.

## Where the CLI is

| Location | Front door | Runtime and schemas |
| --- | --- | --- |
| `artagon-scripts` repository | `python3 scripts/harness-eval.py` | `plugins/artagon-harness-eval/src/artagon_harness_eval/`, `schemas/harness-eval/` |
| Installed plugin | `python3 <plugin>/scripts/harness-eval.py` | `<plugin>/src/artagon_harness_eval/`, `<plugin>/schemas/harness-eval/` |

Always pass `--output json` and branch on `exit_code` and `reason_code` in the `harness-eval-envelope/v1` response. Keep `artagon-harness-eval` in the **operator CLI** only; never inject operator skills into subject workspaces unless explicitly evaluating them.

## Operator command loop

Run one step at a time and preview every campaign before running live trials.

1. `python3 scripts/harness-eval.py --output json nix-check`: verify the staged offline Nix flake inputs (`flake.nix.in`, `flake.lock.in`) and public source allowlist.
2. `python3 scripts/harness-eval.py --output json auth`: inspect cross-OS keyring backend status (`security` on macOS; `secret-tool`, `pass`, or `systemd-creds` on Linux) and store separation without printing secret values.
3. `python3 scripts/harness-eval.py --output json preflight --manifest MANIFEST [--allow-host-pin] [--allow-api-keys] [--allow-live-mcp]`: validate the protocol against `protocol.schema.json`, check arm billing guards, verify vendor-blind judge rules, and confirm harness binaries.
4. `python3 scripts/harness-eval.py --output json freeze --manifest MANIFEST --out FROZEN.json [--allow-host-pin] [--allow-api-keys] [--allow-live-mcp]`: pin harness versions, cassette SHA-256 digests, and deterministic `ABBA` block seeds into `frozen-manifest.schema.json`.
5. `python3 scripts/harness-eval.py --output json run --frozen FROZEN.json --campaign CAMPAIGN_DIR --dry-run`: preview the exact `ABBA` trial schedule and arm assignments with `mutations="none"` and zero model calls.
6. `python3 scripts/harness-eval.py --output json run --frozen FROZEN.json --campaign CAMPAIGN_DIR [--allow-host-pin] [--allow-api-keys] [--allow-live-mcp]`: execute trials inside `0700` `/var/tmp/art-eval-<uid>` roots, fuse 4-layer traces into Parquet/SQLite, run deterministic verifiers (and optional blind judge), and write `summary.json`.
7. `python3 scripts/harness-eval.py --output json status --campaign CAMPAIGN_DIR` and `analyze --campaign CAMPAIGN_DIR`: inspect campaign progress, `ITT` pass rates, `cassette_miss` sensitivity, quota censoring, and Holm-Bonferroni adjusted p-values.

## Exit table

| Code | Constant | Meaning and required operator action |
| --- | --- | --- |
| 0 | `EXIT_OK` | Command succeeded; inspect `data` in the JSON envelope. |
| 2 | `EXIT_SCHEMA_USAGE` | Schema validation failed, required flag missing (`--allow-host-pin`, `--allow-live-mcp`), or self-judging detected; fix manifest or CLI flags. |
| 3 | `EXIT_CREDENTIAL_UNAVAILABLE` | Subscription session or requested keyring credential unavailable; ask the user to authenticate the harness or unlock the store. |
| 4 | `EXIT_BILLING_GUARD` | Metered API/BYOK variable leaked into `subscription` mode, or `api_key` arm lacked `--allow-api-keys` or finite budget cap; scrub env or obtain explicit user authorization. |
| 5 | `EXIT_ISOLATION_CANARY` | Ancestor contamination, fixture quarantine failure, single-exec shim breach, or blind-judge canary leak; stop and inspect isolation diagnostics. |
| 6 | `EXIT_VERIFIER_CASSETTE` | Verifier contract error or `cassette_miss` threshold exceeded; record missing MCP fixture entries or fix verifier script. |
| 7 | `EXIT_INCONCLUSIVE_QUOTA` | Whole-block rate-limit/quota `429` censoring exceeded `20%` (`inconclusive_quota_censored`); wait for subscription quota reset before re-running. |
| 8 | `EXIT_MULTIPLEXER` | Tier-2 `ntm`, `herdr`, or ephemeral `cao-server` multiplexer failed; inspect multiplexer readiness and private `tmux` logs. |

## Three safety rules

1. **Subscription auth is the default**: Never pass `--allow-api-keys` unless the user explicitly approves metered spend and the protocol sets finite `max_cost_usd` or `max_tokens` caps.
2. **Offline cassettes and Nix pins are the default**: Never pass `--allow-live-mcp` or `--allow-host-pin` without explicit operator consent for non-hermetic execution.
3. **Never expose secrets or weaken isolation**: Never print OAuth tokens or API keys, never run subject trials inside a dirty checkout without fixture quarantine, and never bypass exit `4` or `5`.

## Harmless invocation

Example: `Preview the ABBA schedule for examples/four-cli-canary.json; do not execute live model trials.`

Map `inspect` and `preview` requests to `nix-check`, `auth`, `preflight`, `freeze`, `run --dry-run`, and `status`. Report the skill marker `artagon-harness-eval/harness-eval/v1`, emit zero model calls when previewing (`mutations="none"`), and summarize the JSON envelope.
