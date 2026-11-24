# Tasks: Implement Standalone `artagon-skills-eval` Workspace (Phases 1–5)

All tasks operate inside `artagon-skills-eval` with zero edits to consumer repositories. Check off a task only after implementation and verification pass in the same worktree.

## Phase 1: Complete Core Domain, Runtime, Plugins & Nix Staging

- [ ] 1.1 Implement pure `artagon_eval_core.domain` modules (`billing`, `splits`, `protocol`, `auth`, `capability`, `model_spec`, `schedule`, `stats`, `outcome`, `judge_policy`, `trace_models`, `assertions`, `planner`) using strict `FrozenModel`, `Expression`, and `rpds-py` with zero `Any` or I/O imports.
  - Proof: `HYPOTHESIS_PROFILE=ci uv run --frozen pytest packages/artagon-eval-core/tests tests/typing/ --fail-on-skip -q && uv run --frozen mypy && uv run --frozen basedpyright && uv run --frozen lint-imports`
  - Status: not run
- [ ] 1.2 Split typed Effect `Protocol` interfaces under `artagon_eval_core.ports` (`subprocess`, `filesystem`, `custody`, `keyring`, `telemetry`, `scrubber`) and provide deterministic in-memory test fakes.
  - Proof: `uv run --frozen mypy && uv run --frozen basedpyright && uv run --frozen lint-imports && uv run --frozen pytest packages/artagon-eval-core/tests -q`
  - Status: not run
- [ ] 1.3 Implement shared `artagon_eval_core.runtime` primitives (`jcs`, `latch`, `child_env`, `proposer`, `pins`, `patch`, `curation`) eliminating duplicate latches, env builders, and patch verifiers across adapters.
  - Proof: `HYPOTHESIS_PROFILE=ci uv run --frozen pytest packages/artagon-eval-core/tests -m property --fail-on-skip -q && uv run --frozen radon cc -n C packages/artagon-eval-core/src`
  - Status: not run
- [ ] 1.4 Complete `artagon_eval_core.plugins` (`hookspecs`, lazy `importlib.metadata` `PluginRegistry`, and 4-dialect `hooks_compiler`) with fail-closed `AdapterUnavailableError` (`exit 69`).
  - Proof: `uv run --frozen pytest packages/artagon-eval-core/tests --fail-on-skip -q && uv run --frozen lint-imports`
  - Status: not run
- [ ] 1.5 Complete ADR-0006 `artagon_eval_core.packaging` (`staging` with `O_NOFOLLOW` `0700` stager, `selfcheck`, zero-dep AST `boundary_check`) and add `tests/packaging/{test_version_bounds,test_license_guard,test_nix_staging}.py` wired into `flake.nix` `checks.<system>.offline`.
  - Proof: `uv run --frozen pytest tests/packaging/ --fail-on-skip -q && uv run --frozen harness-eval-nix-check --offline`
  - Status: not run

## Phase 2: Core Shell, 5-CLI Decoders, DuckDB Store, Shims & `harness-eval` CLI

- [ ] 2.1 Implement `artagon_eval_core.shell.transcript` (`claude`, `codex`, `agy`, `copilot`, `kimi`, `otel_reducer`, `fusion`) and `shell/multiplexers` (`ntm`, `herdr`, `cao`, `hcom`) keeping every module `<= 300` LOC and `CC <= 8`.
  - Proof: `uv run --frozen pytest packages/artagon-eval-core/tests --fail-on-skip -q && uv run --frozen radon cc -n C packages/artagon-eval-core/src`
  - Status: not run
- [ ] 2.2 Implement `artagon_eval_core.shell` execution & custody modules (`catalog_loader`, `model_resolver`, `workspace`, `custody_fs` with `flock` `<= 3` holdout cap, `materializer`, read-only `keyring`, RFC 8785 `cassette`, loopback `otlp_sink`, `judge_runner`, `trial_executor`).
  - Proof: `HYPOTHESIS_PROFILE=ci uv run --frozen pytest packages/artagon-eval-core/tests --fail-on-skip -q`
  - Status: not run
- [ ] 2.3 Implement `artagon_eval_core.store` (`parquet_writer`, `duckdb_query`, `sql_guard`, `otlp_export`) with pre-redacted 5-table Parquet compaction, holdout split guards, and loopback endpoint checks.
  - Proof: `uv run --frozen pytest packages/artagon-eval-core/tests --fail-on-skip -q`
  - Status: not run
- [ ] 2.4 Complete ADR-0012 hot-path `artagon_eval_core.shims` (`trampoline`, `hook_sink` alongside `wire`, `scrub`) verified under `python -P -s -m` with `<= 5ms` latency and zero heavy imports.
  - Proof: `uv run --frozen pytest -m hotpath --fail-on-skip -q && uv run --frozen lint-imports`
  - Status: not run
- [ ] 2.5 Implement full Typer `harness-eval` subcommands (`cmd_auth`, `cmd_campaign`, `cmd_trace`, `cmd_ops`, `nix-shell`, `schema export`), Py3.9-parseable stdlib `scripts/{harness-eval,harness-eval-nix-check}.py` with billing-var parity tests, and external `--repo-root`/`--config-dir` 4-layer overlay tests in `tests/integration/test_external_repo_targeting.py`.
  - Proof: `uv run --frozen pytest tests/integration/ packages/artagon-eval-core/tests --fail-on-skip -q && uv run --frozen harness-eval --help`
  - Status: not run

## Phase 3: `artagon-eval-skills`, `skills-ref` Linter & Unified `skill-eval` CLI

- [ ] 3.1 Implement `artagon_eval_skills.contracts` (`suite`, `results`, `inventory`, `overlays`) using strict `FrozenModel` with zero import-time disk I/O and fail-closed overlay validation.
  - Proof: `HYPOTHESIS_PROFILE=ci uv run --frozen pytest packages/artagon-eval-skills/tests --fail-on-skip -q`
  - Status: not run
- [ ] 3.2 Implement `artagon_eval_skills.lint` (`portability`, `security` with hidden Unicode + `SecretVault`, `plugin_parity`, `runner`) on top of isolated `spec_adapter.py` and verify `skills-ref` isolation via `lint-imports`.
  - Proof: `uv run --frozen pytest packages/artagon-eval-skills/tests --fail-on-skip -q && uv run --frozen lint-imports`
  - Status: not run
- [ ] 3.3 Implement PyYAML `artagon_eval_skills.generator.emitters` (`eval.yaml`, `tasks/*.yaml`, `trigger_tests.yaml`, `tasks.skillopt.json` with `--check`) and migrate the single canonical 47-file fixture tree to `packages/artagon-eval-skills/tests/fixtures/skill_eval_execution/`.
  - Proof: `uv run --frozen pytest packages/artagon-eval-skills/tests --fail-on-skip -q`
  - Status: not run
- [ ] 3.4 Implement `artagon_eval_skills.workflows` (`lanes_build`, `lanes_run`, `lanes_score`, `gate`, `promote`, `report`, `purge`, `ntm_lab`, `native_compat`) and unified `skill-eval` / `skill-lint` Typer CLIs enforcing holdout quarantine and `GateAccepted -> 100644 promotion.patch`.
  - Proof: `HYPOTHESIS_PROFILE=ci uv run --frozen pytest packages/artagon-eval-skills/tests --fail-on-skip -q && uv run --frozen radon cc -n C packages/artagon-eval-skills/src`
  - Status: not run
- [ ] 3.5 Execute read-only cross-repo parity check (`skill-eval generate --check`, `skill-eval validate-results --all`, `skill-lint --all-plugins`) against an external multi-plugin Agent Skill repository via `--repo-root` and confirm zero hardcoded `artagon-scripts` paths under `packages/*/src/`.
  - Proof: `uv run --frozen pytest tests/integration/ --fail-on-skip -q && ast-grep scan --config sgconfig.yml`
  - Status: not run

## Phase 4: Benchmark/Validation Adapters (`waza`, `skillspec`) & Plugin/APM Packaging

- [ ] 4.1 Implement `packages/artagon-eval-waza` (`compiler/`, `exporter/`, `runner/`, `waza_pin.json`, `plugin.py`) consuming core `runtime/` primitives with isolated `--fail-on-skip` tests.
  - Proof: `uv run --frozen pytest packages/artagon-eval-waza/tests --fail-on-skip -q && uv run --frozen lint-imports`
  - Status: not run
- [ ] 4.2 Implement `packages/artagon-eval-skillspec` (`pin_runner.py`, `phase1_search.py`, `skillspec_pin.json`, `plugin.py`) with isolated `--fail-on-skip` tests.
  - Proof: `uv run --frozen pytest packages/artagon-eval-skillspec/tests --fail-on-skip -q && uv run --frozen lint-imports`
  - Status: not run
- [ ] 4.3 Finalize standalone multi-CLI native plugin and APM manifests (`plugin.json`, `.claude-plugin/{plugin,marketplace}.json`, `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, `.copilot-plugin/plugin.json`, `.kimi-plugin/plugin.json`, `kimi.plugin.json`, `apm.yml`, `apm.lock.yaml`, `EXTENSION.md`) and update `skills/harness-eval*` references for standalone CLI entrypoints.
  - Proof: `uv run --frozen skill-lint --skills-dir skills`
  - Status: not run

## Phase 5: Optimizer/Observability Adapters & `v0.2.0` Release

- [ ] 5.1 Implement `packages/artagon-eval-dspy` (`lm_engine`, `gepa_runner`, `dspy_module`, `quarantine` with zero mutable dicts, `plugin.py`) and isolated `--fail-on-skip` tests.
  - Proof: `uv run --frozen pytest packages/artagon-eval-dspy/tests --fail-on-skip -q && uv run --frozen lint-imports`
  - Status: not run
- [ ] 5.2 Implement `packages/artagon-eval-skillopt` (`gateway`, `patch_merge`, `harvest`, `isolated_main` preserving `python3 -I`, `cli`, `skillopt_pin.json`, `plugin.py`) and verify Nix `.#skillopt` build and `skillopt-runner` proxy parity.
  - Proof: `uv run --frozen pytest packages/artagon-eval-skillopt/tests --fail-on-skip -q && nix build .#skillopt --no-link`
  - Status: not run
- [ ] 5.3 Implement `packages/artagon-eval-evoskill` (`loader` with zero import-time `sys.meta_path` mutation, `solver`, kernel-sandboxed `evolver`, `plugin.py`) and isolated `--fail-on-skip` tests.
  - Proof: `uv run --frozen pytest packages/artagon-eval-evoskill/tests --fail-on-skip -q && uv run --frozen lint-imports`
  - Status: not run
- [ ] 5.4 Implement `packages/artagon-eval-observability` (`phoenix_sink` Apache-2.0 only, `mlflow_sink` `mlflow-tracing` + optional `mlflow-skinny`, `offline_scorer`, `plugin.py`) and verify zero `Elastic-2.0` pulls via `test_license_guard.py`.
  - Proof: `uv run --frozen pytest packages/artagon-eval-observability/tests tests/packaging/test_license_guard.py --fail-on-skip -q`
  - Status: not run
- [ ] 5.5 Add `.github/workflows/release.yml` (SHA-pinned actions, `harden-runner`), expand `.github/workflows/ci.yml` with the 7-leg adapter matrix + `nix-offline` + `plugin-and-apm` jobs, cut `v0.2.0` wheels/sdist/`SHA256SUMS`/`schemas-v0.2.0.tar.gz`, and complete `review.md` and `verification.md` evidence before archiving.
  - Proof: `openspec validate --all --strict && uv run --frozen pytest --cov --fail-on-skip -q && ast-grep test --config sgconfig.yml && ast-grep scan --config sgconfig.yml`
  - Status: not run
