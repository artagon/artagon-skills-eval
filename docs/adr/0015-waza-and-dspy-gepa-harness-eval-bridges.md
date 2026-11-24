---
status: accepted
date: 2026-11-17
decision-makers: ["Artagon Maintainers"]
consulted: []
informed: []
---

# ADR-0015: Integrate Waza v0.41.0 and DSPy 3.4.1 / GEPA v0.1.4 bridges into standalone `artagon-harness-eval`

## Status

Accepted (prerequisite foundation for `@change:add-skill-eval-optimization` and `@adr:0016`).

## Context

`plugins/artagon-harness-eval/` (`@adr:0009`..`@adr:0012`) provides subscription-default multi-CLI execution (`claude`, `codex`, `agy`, `copilot`), 4-layer Parquet/DuckDB trace fusion, `SecretVault` redaction, and offline Nix standalone packaging. Operators need two interoperable capabilities without sacrificing standalone `git subtree split` independence or vendor-blind judging:

1. Bidirectional interoperability with `microsoft/waza` (`v0.41.0`, `d537bf00d4d442a1935ceba2fbc664b9ccb497b2`, `MIT`): compiling 11-grader Waza `eval.yaml` suites (`waza-import`) into `harness-eval-protocol/v1` and exporting compacted 4-layer campaigns into per-arm Waza `EvaluationOutcome` JSON (`trace-export --format waza-outcome`) with relative `0700` redacted workspace bundles (`--snapshot-workspaces`).
2. Candidate skill/prompt optimization over `gepa` (`v0.1.4`, `8b0ce6cd99a234f6b74daf37558a2ac0ce18f975`, `MIT`) and `dspy` (`3.4.1`, `099982b3c3eec9fc4ec4796d49915af42367a253`, `MIT`) via `harness-eval optimize-gepa` (`optimize-anything` and `dspy-gepa`), keeping reflection toolless (`reflect_no_tools`), holdout `test` tasks strictly quarantined, `HTTP 429` quota blocks free of `0.0` Pareto score corruption, and candidate patches strictly unpromoted outside `plugins/`.

## Decision

1. **D1 — Normalized `final_output_text`, Stage-1b `trace_assertions`, Per-Trial Vendor-Blind `judge.panel` Recusal, and Relative `waza-outcome` Bundles**:
   - Normalize bounded (`<= 262144` UTF-8 bytes), `SecretVault`-redacted assistant final response text (`final_output_text`) in `transcript.py` across `headless`, `ntm`, `herdr`, and `cao` runners while excluding tool-call arguments and tool outputs; write `WAZA_OUTPUT_PATH` (`final_output.txt` in `trace_dir`) and `WAZA_WORKSPACE_DIR` (`ws/`) before Stage-1a `_run_task_verifier` (scrubbing verifier stdout/stderr).
   - Evaluate Stage-1b `trace_assertions` (`skill_invocation`, `action_sequence`, `behavior`, `output_regex`, `output_keyword`, `output_json_schema`) post-fusion and combine with Stage-1a into `verified_success`.
   - Support optional `judge.panel` (`minItems: 3`) with per-trial vendor-blind recusal: exclude panel members sharing `harness` or `resolve_vendor_families(..., strict_copilot=True)` vendor family with each trial's candidate arm (re-checking `observed_model`), require `>= 2` non-overlapping panel judges across `>= 2` vendor families (`exit 2` `judge_vendor_conflict` else), aggregate the median over non-recused judges, and record `judge_blindness` + `judge_recused_members`.
   - Order post-campaign execution strictly (Stage-2 judging -> `0700` `--snapshot-workspaces` excluding `.git/`, symlinks, and sibling `/var/tmp` dirs -> final `trace.schema.json` validation & `trace.json` persistence -> `compact_campaign_store` -> `finally` `/var/tmp` cleanup) and export per-arm `EvaluationOutcome` JSON with copied relative `0700` workspace snapshots.
2. **D2 — 11-Grader `waza-import` Compiler and Dual-Copy Execution Fixture Corpus**:
   - Compile Waza `eval.yaml` suites via `harness-eval waza-import` inside `--repo-root` (`--materialize-dir`), gating `code` and `program` graders behind `--trust-suite-code` (`exit 2` `untrusted_waza_grader_code`), rejecting unknown graders (`exit 2` `unsupported_waza_grader`), skipping `trigger_tests.yaml` (`trigger_tests_skipped: true`), and enforcing confined relative paths (`exit 5` `repo_path_escaped`).
   - Add additive `"execution-evals.json"` + `read_execution_skill()` in `configs/skill_eval_inventory.json` and `scripts/lib/skill_eval_contract.py` (`tiers.execution.supported: false` preserved for legacy scorers) with byte-identical fixture directories in `tests/fixtures/skill_eval_execution/` and `plugins/artagon-harness-eval/tests/fixtures/skill_eval_execution/`.
3. **D3 — Full-Override `reflect_no_tools`, Optional `[dspy]` Extra, `GEPAConfig` / `HarnessEvalDSPyModule`, and Pre-Spawn `CampaignAbortLatch`**:
   - Replace `base_flags` and `tier2_common_flags` completely under `reflect_no_tools` without any `--dangerously-*`, `--allow-all`, `--yolo`, or approval-bypass flags (`exit 5` `reflection_tools_not_disabled` on probe/canary failure or nonzero reflector tool/MCP calls; `exit 6` `reflection_process_failed` on nonzero exit), fence `64 KiB` redacted `ASI` in random-nonce `<UNTRUSTED_TRAJECTORY_DATA>`, enforce HMAC `[ahe_provenance ...]` split quarantine, and confine candidate edits to `SKILL.md` and `references/*.md` (`exit 5` `reflection_path_escaped`).
   - Declare optional `[project.optional-dependencies].dspy = ["gepa>=0.1.4,<0.2", "dspy>=3.4.1,<3.5"]` (exempt from `locked-versions.json`, verified via dedicated `--fail-on-skip` CI leg), implement `bridges/dspy_gepa.py` (`GEPAConfig` `optimize_anything` + lazy mutable `HarnessEvalDSPyModule` + `BoundedProviderSemaphore` `<= 2`), enforce `max_cli_launches` (`exit 4` `launch_budget_exceeded`) and `BaseException` `CampaignAbortLatch` (`exit 7` `inconclusive_quota_censored` terminating active process groups without `0.0` score substitution), and emit unpromoted `candidate.patch` + `candidate-bundle.json` strictly outside `plugins/` (`exit 5` `out_dir_inside_plugins`).

## Alternatives considered

| Option | Pros | Cons | Outcome |
|---|---|---|---|
| Native `bridges/{waza,dspy_gepa}.py` + Stage-1b `trace_assertions` + recused `judge.panel` + optional `[dspy]` extra | Preserves offline `--no-extra` Nix split independence, vendor-blind judging across 4+ CLIs, and exact `v0.41.0` / `v0.1.4` / `3.4.1` wire contracts. | Requires Stage-1b assertion evaluator, `CampaignAbortLatch` process-group hooks, and dual-copy fixtures. | Chosen |
| Put `dspy` and `gepa` in core `[project].dependencies` | Avoids `pytest.importorskip` and extra CI leg. | Pulls LiteLLM/cloud transitive dependencies into the offline Nix closure, violating `@adr:0012`. | Rejected |
| Require a 5th external API judge for 4-CLI campaigns | Simple single-judge configuration. | Requires metered API keys instead of recusing subscription CLI judges per trial. | Rejected |

## Consequences

- Good, because 4-CLI subscription campaigns gain self-contained `judge.panel` recusal, fileless output/trajectory assertions, Waza `v0.41.0` import/export parity, and budget/quota-safe GEPA candidate generation while keeping `--no-extra dspy` standalone builds untouched.
- Bad, because optional `[dspy]` tests require `--fail-on-skip` CI enforcement and dual-copy execution fixtures must stay byte-identical across monorepo and plugin trees.
- Neutral, because `optimize-gepa` emits only unpromoted candidate bundles outside `plugins/`, leaving automated multi-CLI holdout promotion to `@change:add-skill-eval-optimization` (`@adr:0016`).

## Links to OpenSpec change

- Change: `@change:integrate-waza-dspy-harness-eval`
- Downstream extension: `@change:add-skill-eval-optimization` (`@adr:0016`)
- Proposal: `openspec/changes/archive/2026-11-18-integrate-waza-dspy-harness-eval/proposal.md`
- Design: `openspec/changes/archive/2026-11-18-integrate-waza-dspy-harness-eval/design.md`
- Tasks: `openspec/changes/archive/2026-11-18-integrate-waza-dspy-harness-eval/tasks.md`

## Links to affected requirements

- `@spec:capability-harness-core`
- `@spec:standalone-harness-eval-package`
- `@spec:waza-harness-eval-bridge`
- `@spec:skillopt-multi-cli-bridge`
- `@spec:dspy-gepa-harness-bridge`

## Links to tests and evidence

- Upstream pin matrix: `openspec/changes/archive/2026-11-18-integrate-waza-dspy-harness-eval/research/upstream-api-pins.md`
- Golden fixtures: `plugins/artagon-harness-eval/tests/fixtures/waza/PROVENANCE.json`, `plugins/artagon-harness-eval/tests/fixtures/gepa/PROVENANCE.json`
- Test suites: `plugins/artagon-harness-eval/tests/test_ahe_stage1b_and_panel.py`, `plugins/artagon-harness-eval/tests/test_ahe_waza_export.py`, `plugins/artagon-harness-eval/tests/test_ahe_waza_import.py`, `plugins/artagon-harness-eval/tests/test_ahe_skillopt_proposal.py`, `plugins/artagon-harness-eval/tests/test_ahe_gepa_optimize_anything.py`, `plugins/artagon-harness-eval/tests/test_ahe_dspy_gepa_module.py`

## Supersedes / superseded by

- Supersedes: N/A
- Superseded by: N/A (extended on `surface: "skill_eval"` by `@adr:0016`)

## Compliance checks

- [x] Implementation matches the decision.
- [x] Design links this ADR.
- [x] Requirements impacted by this decision are linked.
- [x] Evidence verifies the decision where applicable.
- [x] Repository references are project-root-relative or symbolic.
