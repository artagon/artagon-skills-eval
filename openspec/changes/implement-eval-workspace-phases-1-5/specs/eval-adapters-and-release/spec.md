# Capability: eval-adapters-and-release

## ADDED Requirements

### Requirement: Mutually Independent Benchmark and Validation Adapters (`waza`, `skillspec`)
`artagon-eval-waza` (`compiler/`, `exporter/`, `runner/`, `waza_pin.json`) and `artagon-eval-skillspec` (`pin_runner`, `phase1_search`, `skillspec_pin.json`) SHALL register via `artagon_eval.benchmarks`, `artagon_eval.sinks`, and `artagon_eval.optimizers` entry points, consume core `runtime/` primitives (zero duplicate latches/env builders), and import zero sibling adapter packages.

#### Scenario: Running isolated benchmark adapter matrix leg with zero skips
- GIVEN a virtual environment containing `artagon-eval-core`, `artagon-eval-skills`, and `artagon-eval-waza` only
- WHEN `pytest --fail-on-skip` and `lint-imports` execute
- THEN all Waza compiler/exporter/runner tests SHALL pass with `0` skipped tests and `0` cross-adapter imports.

### Requirement: Isolated Optimizer Adapters (`dspy`, `skillopt`, `evoskill`)
`artagon-eval-dspy`, `artagon-eval-skillopt`, and `artagon-eval-evoskill` SHALL run as independent Pluggy packages registering via `artagon_eval.optimizers`. `QuarantinedOptimizerCorpus` SHALL reject `TestEvalCase` and mutable dicts; `skillopt` SHALL preserve `python3 -I` isolation and Nix `.#skillopt`; `evoskill` SHALL scope dist loading without import-time `sys.meta_path` mutation.

#### Scenario: Importing artagon-eval-evoskill leaves sys.meta_path unchanged
- GIVEN a Python process before and after `import artagon_eval_evoskill`
- WHEN `sys.meta_path` is compared
- THEN `sys.meta_path` SHALL remain identical until scoped loader execution explicitly runs and cleans up.

#### Scenario: Proxying skillopt-runner when adapter is absent
- GIVEN an installation without the `[skillopt]` extra
- WHEN `skillopt-runner --help` or an execution command runs
- THEN `artagon_eval_core.cli.skillopt_proxy` SHALL fail closed with exit code `69` (`AdapterUnavailableError`) rather than raising `ModuleNotFoundError`.

### Requirement: Apache-2.0 Observability Adapter (`observability`)
`artagon-eval-observability` (`phoenix_sink`, `mlflow_sink`, `offline_scorer`, `plugin.py`) SHALL depend strictly on Apache-2.0 Phoenix packages (`arize-phoenix-otel`, `arize-phoenix-client`, `openinference-semantic-conventions`) and `mlflow-tracing` (with optional `mlflow-skinny`), never pulling `Elastic-2.0` `arize-phoenix`.

#### Scenario: Verifying zero Elastic-2.0 packages in observability matrix leg
- GIVEN an isolated environment with `artagon-eval-observability` installed
- WHEN `tests/packaging/test_license_guard.py` executes
- THEN zero distributions SHALL carry `Elastic-2.0` and zero `arize-phoenix` core server distributions SHALL be present.

### Requirement: Standalone Multi-CLI Plugin, APM Manifests, and `v0.2.0` Release Artifacts
The repository SHALL ship synchronized standalone manifests (`plugin.json`, `.claude-plugin/{plugin,marketplace}.json`, `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, `.copilot-plugin/plugin.json`, `apm.yml`, `apm.lock.yaml`, `EXTENSION.md`) pointing to `skills/` with zero legacy monorepo paths. `.github/workflows/release.yml` SHALL build deterministic `v0.2.0` wheels, sdist, `SHA256SUMS`, and exported `schemas-v0.2.0.tar.gz`.

#### Scenario: Validating standalone skills and plugin manifests in CI
- GIVEN the repository checkout with updated standalone `skills/harness-eval*` and plugin manifests
- WHEN `skill-lint --plugin-dir .` runs
- THEN Tier-0 (`skills-ref`), Tier-1, and Tier-2 manifest parity checks SHALL pass with zero broken links or legacy `plugins/artagon-harness-eval/` references.
