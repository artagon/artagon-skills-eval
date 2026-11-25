---
status: accepted
date: 2026-11-18
decision-makers: ["Artagon Maintainers"]
consulted: []
informed: []
---

# ADR-0016: Consolidate skill evaluation onto subscription-only CLI execution, Apache-2.0/MIT adapters, and post-run OTLP sinks

## Status

Accepted (`@change:integrate-waza-dspy-harness-eval` and `@adr:0015` archived at `openspec/changes/archive/2026-11-18-integrate-waza-dspy-harness-eval/`; all Phase-A and Phase-B implementation and verification tasks `0.1`..`5.7` verified under `@change:add-skill-eval-optimization`).

## Context

Skill evaluation across `artagon-scripts` previously spanned manual pane-driven scripts (`scripts/skill-eval-lanes.py`, `scripts/skill-experiments.py`), a single-turn wrapper (`scripts/skill-eval-cli.py`), `66` retired/API-key-bound artifacts under `plugins/artagon-python/` (`14` broken `inspect_ai` `skills/*/tasks/skill_eval.py` wrappers, `28` `optimization/*.py` scripts, `10` `evaluation-runtime/` files, and `14` metered `promptfooconfig.yaml` configs), and post-run trace exporters in `plugins/artagon-harness-eval/src/artagon_harness_eval/store.py` whose HTTP wire formats failed against Arize Phoenix `21.0.0` (`HTTP 415` on JSON instead of `application/x-protobuf`) and MLflow `3.18.0` (`HTTP 422` missing `x-mlflow-experiment-id` and standard OTLP `/v1/traces`).

While `@adr:0009` Decision 4 allows general `artagon-harness-eval` campaigns (`surface: "general"`) to opt into `auth_mode="api_key"` with `--allow-api-keys` and a finite dollar budget, operators explicitly require repository skill evaluation, benchmarking, judging, and optimization (`surface: "skill_eval"` / `--subscription-only`) across `claude`, `codex`, `copilot`, and `agy` to run **exclusively** on signed-in CLI subscriptions (`0` metered API keys), require zero live Docker/ClickHouse/PostgreSQL servers during trials (`@adr:0010`, `@adr:0011`), preserve `MIT` standalone offline Nix `git subtree split` independence (`@adr:0012`), and sequence cleanly after `@change:integrate-waza-dspy-harness-eval` (which proposes ADR-0015).

## Decision

1. **D1 — Unified Front Door, 4-Harness Schema Alignment, and Legacy Retirement**: Route automated skill evaluation through `scripts/skill-eval.sh` over `plugins/artagon-harness-eval/`, align `SUPPORTED_HARNESSES` and all `7` harness-scoped Draft 2020-12 JSON Schemas on the 4 active CLIs (`claude`, `codex`, `agy`, `copilot`; `3` byte-identical schema directories: `schemas/harness-eval/`, `plugins/artagon-harness-eval/schemas/harness-eval/`, and `plugins/artagon-harness-eval/src/artagon_harness_eval/data/schemas/`; `trace.json` remains `v1` with `"otel"` omitted from `layers_present`), retain `scripts/skill-experiments.py` solely for interactive NTM lab workflows (`@change:add-scientific-skill-experiments`), shim `scripts/skill-eval-lanes.py` and `scripts/skill-eval-cli.py` onto run-local artifacts, and retire all `66` `inspect_ai`/optimization/`promptfooconfig.yaml` files in `plugins/artagon-python/` (`excluded_files` `15 -> 81`, preserving `source_plugin_file_count == 158`).
2. **D2 — Explicit `surface: "skill_eval"` Narrowing of `@adr:0009` Decision 4 and Enumerated Child Env Allowlist**: Introduce `surface: "skill_eval"` (`subscription_only: true` / `--subscription-only`), passed unconditionally by `scripts/skill-eval.sh`, `skillopt_main.py`, and all skill adapters/sinks, so `auth_mode="api_key"`, `--allow-api-keys`, `--allow-env-only-billing`, `EVOSKILL_CC_TOKEN_FILE`, `DAYTONA_API_KEY`, `OPENROUTER_API_KEY`, short/long `COPILOT_*` BYOK variables, and all `30` `METERED_BILLING_ENV_VARS` / `3` prefixes fail closed with `EXIT_BILLING_GUARD` (`4`, `api_keys_not_allowed` / `subscription_forbids_metered_env` / `subscription_metered_env_detected`; `<harness>_subscription_missing` `exit 3`), while preserving `surface: "general"` for standalone `artagon-harness-eval` campaigns, and spawn adapter/sink child processes under an explicit environment allowlist without prefix wildcards.
3. **D3 — Two-Root Isolation, Default-Deny Kernel Evolver Allowlist, and Non-Keyring `0600` Supervisor HMAC Custody**: Keep trial, solver, reflector, and Evolver working roots under `/var/tmp/art-eval-<uid>/` outside the repository (`verify_ancestors=True`, `gate` serializing `gate-*` root creation and sweep under `.gate-sweep.lock` to sweep `gate-*` roots lacking a live `flock(LOCK_EX)` on `.owner.lock` at startup and deleting `/var/tmp` `test` roots in `finally`, extended read canary blocking `**/evals/**`, `.git/`, `scratch/**`, supervisor `$XDG_STATE_HOME/**`, and sibling `/var/tmp/art-eval-*`) while storing only post-trial receipts, manifests, reports, and target-skill `100644` text patches (`promotion.patch`) in `0700` `scratch/skill-eval/<run_id>/` (`exit 5` `out_dir_inside_plugins` inside `plugins/`, `run_dir_outside_scratch` elsewhere outside `scratch/skill-eval/`). Require OS kernel confinement (`os_sandbox_active == True`) configured as a default-deny read allowlist (`<evolver_root>` + read-only toolchain only) for tool-enabled `EvoSkill v2` Evolver runs (`exit 5` if unavailable; `--allow-unsandboxed-candidates` allows only toolless `reflect_no_tools` mutation, and whenever any trial or Evolver ran with `os_sandbox_active == False`, `{holdout,manifest,ledger}_integrity` all record `"unverified_unsandboxed"` vs `"verified_sandboxed"` when all ran kernel-sandboxed). Because `keyring.py` projects the default unlocked Secret Service collection to Linux subscription trials, store per-campaign `32`-byte CSPRNG HMAC keys (`hmac/campaigns/<id>.key` with `campaign_id == run_id`, minted at campaign start, passed in-memory to `SkillOptProposalFn`, deleted with `<run_dir>` by offline `purge-campaign`, and signing sidecar `provenance_header` stripped before prompt delivery) and the long-lived holdout ledger key (`hmac/ledger.key` + `hmac/ledger_initialized`, signing pre-staging `holdout_ledger.json` under `flock(LOCK_EX)` + atomic `os.replace` capped at `<= 3` `gate` calls per `(skill_id, test_digest)`) exclusively in `0600` files inside `0700` `$XDG_STATE_HOME/artagon-harness-eval/hmac/` outside host/trial keyrings and `/var/tmp`-projected trial `XDG_STATE_HOME`.
4. **D4 — Four Proposal-Only Subscription-CLI Adapters (Phase-B Sequenced After `@change:integrate-waza-dspy-harness-eval` Archives)**:
   - `SkillOpt 0.2.0` (`MIT`): `scripts/skill-eval.sh` (`configs/skillopt_pin.json` `exit 69`; `skillopt-sleep dry-run` permitted, while `run`/`adopt`/`schedule`/`--auto-adopt` exit `64`) + isolated `python3 -I` `scripts/skill_eval/skillopt_main.py` (`--harness-eval-src`), routing both `EnvAdapter` (`rollout`, `reflect`) **and** non-adapter trainer stages (`merge_patches`, `chat_optimizer`, slow/meta updates) through one guarded subscription gateway (`bridges.skillopt`).
   - `EvoSkill v2.0.0` (`Apache-2.0`, `[evoskill]`): `bridges/evoskill.py` (`importlib.metadata.version("evoskill") == "2.0.0"`), `k`-attempt local 4-CLI solver (`train`/`val`), default-deny kernel read-allowlisted Evolver (`--stop-after evolve`).
   - `Waza v0.41.0` (`MIT`, `configs/waza_pin.json` verified at `scripts/skill-eval.sh`): offline `mock` (`plumbing_only: true`), live `copilot-sdk` (`copilot login`, short `COPILOT_*` refused `exit 4`), and live `harness-eval` (`waza-import` / `waza-outcome`, forwarding `--hash-holdout-payloads` when `--allow-unsplit-v1` is set).
   - `pyDSP` (`[dspy] = ["gepa>=0.1.4,<0.2", "dspy>=3.4.1,<3.5"]`, `MIT`): `bridges/pydsp.py` sync/async `HarnessCliDSPyEngine` (`complete(Request) -> Response`, pre-launch AND sync/async per-call presence-aware `(call_kwargs["lm"] if "lm" in call_kwargs else predictor.lm) or dspy.settings.lm` + `dspy.context` effective LM verification including sync/async `predict(..., lm=None)` socket-trap checks, allowing `reflection_lm=None` paired with factory `SkillOptProposalFn`) + `bridges/dspy_gepa.py` + `SkillSpec` Phase-1 4-intent search.
5. **D5 — Repaired OTLP Wire Exporters and Allowlisted Post-Run Sinks**: Construct Phoenix `21.0.0` `ExportTraceServiceRequest` (`application/x-protobuf`) with exact `bytes.fromhex()` 16/8-byte trace/span IDs, OpenInference `0.1.46` skill metadata, and `arrayValue` tags; send MLflow `3.18.0` standard OTLP `/v1/traces` with `x-mlflow-experiment-id`; fail closed (`exit 5` `unredacted_trace_export`) if `redaction_applied` is missing or not `True`; preserve redacted `surface: "general"` non-`v2` exports without `split` while refusing `contract_version == "artagon/skill-evals/v2"` protocols/traces missing `surface` (`exit 5`), unsplit `skill_eval` exports (`exit 2` `invalid_task_split` unless `--allow-unsplit-v1` + `--hash-holdout-payloads`), and raw `test`/`holdout` trace exports (`exit 5` `holdout_split_contaminated`) across all `5` formats unless `--hash-holdout-payloads` replaces all six text fields with supervisor `"hmac-sha256:<hex>"`; enforce `_validate_export_endpoint` loopback checks; and accept only bridge-factory offline `BridgeScorer` objects (`predict_fn=None`, `0` live model calls; any other scorer/judge exits `4`).
6. **D6 — Four-Step Default-Deny Permissive SPDX Guard**: Restrict direct `[project.optional-dependencies]` (`[dspy]`, `[evoskill]`, `[mlflow]`, `[phoenix]`) to `MIT` and `Apache-2.0`, and evaluate `uv.lock`/`.venv` distributions in strict order (`License-Expression` -> exact/normalized `License` -> OSI `Classifier` -> `name==version`+`sha256` reviewed overrides; `OR` `>= 1` admitted, `AND` all admitted, `WITH` override-only) against `{MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, 0BSD, ISC, PSF-2.0, MPL-2.0, Zlib, Unlicense}` (passing all `63` installed core/dev distributions and rejecting `ELv2`, `SSPL-*`, `AGPL-*`, `GPL-*`, `LGPL-*`, `LicenseRef-*`, and unreviewed `UNKNOWN`).

## Alternatives considered

| Option | Pros | Cons | Outcome |
|---|---|---|---|
| Unified `scripts/skill-eval.sh` + `artagon-harness-eval` + subscription-only adapters (`SkillOpt`, `EvoSkill v2`, `Waza`, `pyDSP`) + `Apache-2.0` post-run OTLP/callable bridges (`MLflow 3.18`, `Phoenix` client) | Enforces zero-API-key subscription execution, `@adr:0011` local DuckDB trial purity, `@adr:0012` permissive offline Nix independence, and one 4-CLI `ITT` paired promotion gate. | Requires adapter gateways for `SkillOpt` `merge_patches`, `EvoSkill v2` default-deny kernel Evolver confinement, and `DSPy 3.4.1` `dspy.lm15` `Engine`. | Chosen |
| Adopt `Inspect AI 0.3.290` + `Inspect SWE 0.3.0` as the live skill evaluation harness | Strong Docker/K8s sandboxes and `pass@k` metrics under `MIT`. | `sandbox_agent_bridge()` suppresses CLI OAuth with dummy API keys; `0` CLI-subscription `ModelAPI` providers exist; lacks `copilot` and `agy` CLI solvers. | Rejected |
| Adopt `OpenLIT 2.1.1` or `o11y-dev/opentelemetry-hooks 0.15.0` for multi-CLI hooks and evaluation | Prebuilt 4-vendor Go CLI hooks and 11 server-side LLM judges. | Requires ClickHouse + metered Vault keys for `openlit.eval()`; misses Codex `"Bash"` (`#1784`); breaks `agy` `{"decision":"allow"}` stdout contract. | Rejected |
| Adopt `Langfuse v4.82.0` as canonical skill bundle store and experiment runner | MIT Annotation Queues and Cohen's Kappa judge analytics. | Requires 6 Docker containers, drops `0755` script modes and extensionless files, and requires metered server keys for LLM judges. | Rejected |
| Add `arize-phoenix` and `arize-phoenix-evals` directly to `artagon-harness-eval` dependencies | Bundled local UI and LLM eval templates. | Both packages carry non-OSI `ELv2` licenses and metered SDK dependencies incompatible with `MIT` distribution and subscription-only policy. | Rejected |

## Consequences

- Good, because every skill benchmark, optimizer (`SkillOpt`, `EvoSkill v2`, `pyDSP`/`GEPA`, `SkillSpec`), judge, and promotion gate executes strictly on signed-in 4-CLI subscriptions (`surface: "skill_eval"`) with non-keyring `0600` supervisor HMAC binding, `/var/tmp` holdout separation, and zero `plugins/` auto-mutation.
- Good, because repairing `store.py` (`bytes.fromhex` `application/x-protobuf` + OpenInference `0.1.46` skill metadata for Phoenix; standard OTLP `/v1/traces` + `x-mlflow-experiment-id` for MLflow `3.18`) unlocks local trace waterfalls, `train`/`val` dataset curation, and paired Wilcoxon/McNemar/BCa diagnostics while leaving general non-skill campaigns untouched.
- Bad, because optional extras (`[dspy]`, `[evoskill]`, `[mlflow]`, `[phoenix]`) require dedicated hash-pinned `--fail-on-skip` CI legs alongside the default `--no-extra` offline Nix suite, and Phase-B tasks must sequence after `@change:integrate-waza-dspy-harness-eval` archives.
- Bad, because hosts without OS kernel sandboxing (`os_sandbox_active == False`) cannot run tool-enabled `EvoSkill v2` Evolver sessions (`exit 5`) and must use toolless `reflect_no_tools` mutation (`--allow-unsandboxed-candidates`) with `{holdout,manifest,ledger}_integrity: "unverified_unsandboxed"` recorded in `gate` verdicts.
- Neutral, because canonical skill authoring and `0755` executable distribution remain in Git and APM `0.29.0` (`scripts/generate-apm-exports.py`), with external registries limited to optional `hasattr`-gated read-only `GitSource` pointers.

## Links to OpenSpec change

- Change: `@change:add-skill-eval-optimization`
- Prerequisite sibling change: `@change:integrate-waza-dspy-harness-eval` (proposes ADR-0015; archives first)
- Proposal: `openspec/changes/add-skill-eval-optimization/proposal.md`
- Design: `openspec/changes/add-skill-eval-optimization/design.md`
- Tasks: `openspec/changes/add-skill-eval-optimization/tasks.md`

## Links to affected requirements

- `@spec:capability-harness-core`
- `@spec:standalone-harness-eval-package`
- `@spec:skill-evaluation-pipeline`
- `@spec:skill-observability-and-eval-sinks`
- `@spec:skillopt-evaluation-adapter`
- `@spec:evoskill-subscription-adapter`
- `@spec:waza-benchmark-adapter`
- `@spec:pydsp-cli-adapter`

## Links to tests and evidence

- Evidence: `@evidence:add-skill-eval-optimization#validation`
- Spec validation receipt: `openspec/changes/add-skill-eval-optimization/evidence/validation/spec-gates.json`
- Research summary: `openspec/changes/add-skill-eval-optimization/evidence/research/summary.md`
- Adversarial review: `openspec/changes/add-skill-eval-optimization/evidence/adversarial-review/`
- Test summary (upon implementation): `openspec/changes/add-skill-eval-optimization/evidence/tests/test-summary.md`

## Supersedes / superseded by

- Supersedes: N/A
- Superseded by: N/A
- Narrows: `@adr:0009` Decision 4 (`--allow-api-keys`) to unconditional subscription-only refusal (`exit 4` `api_keys_not_allowed`) when `surface == "skill_eval"` (`--subscription-only`); Task `5.5` appends a cross-link back-reference to `docs/adr/0009-harness-eval-dual-auth-and-keychain-separation.md` upon acceptance.

## Compliance checks

- [x] Implementation matches the decision.
- [x] Design links this ADR.
- [x] Requirements impacted by this decision are linked.
- [x] Evidence verifies the decision where applicable.
- [x] Repository references are project-root-relative or symbolic.
