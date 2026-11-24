---
status: accepted
date: 2026-11-14
decision-makers: []
consulted: []
informed: []
---

# ADR-0009: Enforce fail-closed subscription default, opt-in API-key staging, and keyring store separation

## Status

Accepted.

## Context

Operators evaluate `claude`, `codex`, `agy`, and `copilot` primarily under
first-party subscription accounts, yet developers frequently keep metered API keys
in shell environments or unlocked default keyrings. Silent fallback to metered
API keys invalidates subscription cost/quota behavior and risks unexpected spend,
while blanket refusal of API keys blocks controlled API-tier benchmarking. On
Linux, exposing the host session D-Bus socket directly lets subject processes
mutate or enumerate unrelated Secret Service collections.

## Decision

1. Default every evaluation arm to `auth_mode: "subscription"`. Scrub all metered
   API-key and BYOK variables in both the supervisor and pre-exec trampoline and
   abort with exit code `4` on any violation.
2. Separate `CLAUDE_EVAL_OAUTH_TOKEN` from `keychain::load_api_keys()`. Require
   metered API keys to reside outside the default unlocked keyring (locked macOS
   keychain or Linux `pass` / locked Secret Service collection); otherwise stamp
   `billing_guard: "env_only"` and require an OS container for scored shell runs.
3. On Linux `subscription` runs needing Secret Service access, project a
   per-trial read-only `xdg-dbus-proxy` at `/tmp/art-dbus-<rand>/bus` (`< 100`
   bytes) allowing read/lookup calls only and terminating on supervisor exit.
4. Permit `auth_mode: "api_key"` only when declared in the manifest with finite
   `max_cost_usd` or `max_tokens` AND `--allow-api-keys` on the CLI. Stage the
   resolved secret in a `0400` `<trial>/secret/api_key` file (bypassing CAO
   `forwarded_env.py` rejections), unlink it before trial completion, and project
   zero subscription OAuth state or keyring IPC.

## Alternatives considered

- Chosen: fail-closed `subscription` default + dual-gated `0400` file-staged
  `api_key` mode + read-only `xdg-dbus-proxy`.
- Rejected: ambient environment forwarding, which leaks keys into CAO HTTP
  requests (`HTTP 422`) and mixes billing modes.
- Rejected: unfiltered Linux session D-Bus access, which exposes unrelated
  secrets and write methods.

## Consequences

Billing mode provenance is explicit and auditable in every frozen manifest and
`shim-exec.json` receipt. Operators running `api_key` evaluations must pass
`--allow-api-keys` and set finite budgets.

## Links to OpenSpec change

- `@change:add-subscription-harness-eval`
- `openspec/changes/add-subscription-harness-eval/proposal.md`
- `openspec/changes/add-subscription-harness-eval/design.md`
- `openspec/changes/add-subscription-harness-eval/tasks.md`

## Links to affected requirements

- `@spec:subscription-harness-evaluation#subscription-authentication-is-the-fail-closed-default`
- `@spec:subscription-harness-evaluation#api-key-mode-requires-explicit-dual-opt-in-and-finite-budget`
- `@spec:subscription-harness-evaluation#mixed-billing-comparisons-are-gated-and-flagged`

## Links to tests and evidence

Verified by `tests/test_harness_eval_contract.py`, `tests/keychain-backend.bats`,
`tests/lib-keychain-linux.bats`, `tests/test_keychain_store_properties.py`, and
`tests/test_harness_eval_trampoline.py`.

## Supersedes / superseded by

- Supersedes: N/A
- Superseded by: Narrowed by `@adr:0016` (`docs/adr/0016-unified-subscription-skill-eval-and-adapter-architecture.md`) on `surface: "skill_eval"` (`--subscription-only`), where Decision 4's opt-in `auth_mode: "api_key"` and `--allow-api-keys` paths are unconditionally refused (`exit 4` `api_keys_not_allowed`); general non-skill harness benchmarking (`surface: "general"`) retains Decision 4 unchanged.
