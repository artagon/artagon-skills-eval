# Proposal: Implement Standalone `artagon-skills-eval` Workspace (Phases 1–5)

## Why

Prior evaluation tooling in `artagon/artagon-scripts` grew across four overlapping subsystems, duplicate Nix flakes, triple-mirrored JSON schemas, `sys.path.insert` workarounds, 1,600+ untyped `dict[str, Any]` annotations, drifted metered-billing env lists, and monolithic multi-thousand-line bridge modules fused into core packaging.

Phase 0 bootstrapped `artagon-skills-eval` as a clean greenfield `uv` workspace and root Nix flake (`docs/PROVENANCE.md`), seeding canonical schemas/catalogs, strict `FrozenModel`/`Expression`/`RedactedStr` domain primitives, `spec_adapter.py`, six adapter package stubs, `ast-grep` rules, `import-linter` contracts, and Hypothesis property-test foundations. Completing Phases 1–5 inside this standalone repository turns the bootstrapped spine into a production-ready `v0.2.0` evaluation platform with zero modifications to consumer repositories until Phase 6 cutover.

## What Changes

- **Phase 1 — Complete Core Foundation & Nix Packaging (`packages/artagon-eval-core/`, `flake.nix`, `tests/packaging/`):** Implement the remaining pure `domain/` modules (`billing`, `splits`, `protocol`, `auth`, `capability`, `model_spec`, `schedule`, `stats`, `outcome`, `judge_policy`, `trace_models`, `assertions`, `planner`), typed effect `ports/`, shared `runtime/` primitives (`jcs`, `latch`, `child_env`, `proposer`, `pins`, `patch`, `curation`), lazy Pluggy `plugins/` (`hookspecs`, `registry`, `hooks_compiler`), ADR-0006 `O_NOFOLLOW` host stager and AST boundary check (`packaging/{staging,selfcheck,boundary_check}`), and packaging/SPDX/version-bounds tests.
- **Phase 2 — Core Imperative Shell, Trace Store, Shims & `harness-eval` CLI (`packages/artagon-eval-core/`, `scripts/`, `tests/integration/`):** Implement 4-CLI transcript decoders (`claude`, `codex`, `agy`, `copilot`, OTel reducer, 4-layer fusion), multiplexer drivers (`ntm`, `herdr`, `cao`, `hcom`), workspace/custody/keyring/cassette/OTLP/judge/trial shell modules, 4-layer DuckDB/Parquet store and OTLP exporter, ADR-0012 `-P -s -m` hot-path `shims/{trampoline,hook_sink}`, full Typer `harness-eval` CLI + Py3.9-parseable stdlib launchers, and external `--repo-root`/`--config-dir` 4-layer overlay targeting.
- **Phase 3 — Skill Evaluation Platform & Unified `skill-eval` CLI (`packages/artagon-eval-skills/`):** Implement frozen `eval-v2` suite/result/inventory/overlay contracts (zero import-time disk I/O), Tier-1/Tier-2 linters on top of `skills-ref` `spec_adapter.py`, PyYAML suite emitters, decomposed lane/gate/promote/report/purge/NTM-lab workflows, unified `skill-eval` and `skill-lint` CLIs, and the single canonical 47-file execution fixture set.
- **Phase 4 — Benchmark/Validation Adapters & Standalone Plugin/APM Packaging (`packages/artagon-eval-{waza,skillspec}/`, `skills/`, `apm.yml`, `.*-plugin/`):** Implement decoupled `artagon-eval-waza` and `artagon-eval-skillspec` Pluggy adapters consuming core runtime primitives, finalize standalone multi-CLI native plugin + APM manifests, and update portable `skills/harness-eval*` references for standalone commands.
- **Phase 5 — Optimizer/Observability Adapters & `v0.2.0` Release (`packages/artagon-eval-{dspy,skillopt,evoskill,observability}/`, `.github/workflows/release.yml`):** Implement decoupled `artagon-eval-dspy`, `artagon-eval-skillopt` (preserving `python3 -I` isolation and Nix `.#skillopt`), `artagon-eval-evoskill` (zero import-time `sys.meta_path` mutation, kernel sandbox), and Apache-2.0-only `artagon-eval-observability` (`phoenix` + `mlflow`), then verify release workflow packaging for `v0.2.0` (wheels, `SHA256SUMS`, exported JSON schema bundle).

### Explicit Boundaries

- **In scope:** All packages, Nix packaging, portable Agent Skills, tests, and release packaging inside `artagon-skills-eval` (Phases 1–5).
- **Out of scope:** Consumer repository shims and legacy retirement in `artagon/artagon-scripts` (Phases 6–7, tracked separately after `v0.2.0`), optional `uv2nix`, `artagon-eval-pydantic-evals`, and `sqlglot` AST SQL guard (deferred to Phase 8).

## Capabilities

### New Capabilities

- `eval-core-foundation`: Pure FCIS domain models, typestates, single canonical billing/split/redaction primitives, Pluggy lazy registry, and ADR-0006 offline Nix packaging and SPDX/version-bounds guards.
- `harness-eval-runtime`: 4-CLI transcript decoders, multiplexers, DuckDB/Parquet trace store, OTLP export, ADR-0012 hot-path shims, full `harness-eval` CLI, and external repository overlay targeting.
- `skill-eval-platform`: `skills-ref` Tier-0 isolation, Tier-1/2 linting, frozen `eval-v2` contracts, PyYAML generators, holdout quarantine gate and promotion patch workflows, and `skill-eval`/`skill-lint` CLIs.
- `eval-adapters-and-release`: Six mutually independent lazy Pluggy adapters (`waza`, `skillspec`, `dspy`, `skillopt`, `evoskill`, `observability`), standalone multi-CLI plugin/APM manifests, and `v0.2.0` release packaging.

## Success criteria

- Every workspace package satisfies `ruff check`, `ruff format --check`, `mypy --strict`, `basedpyright --strict` (`reportAny=error`, `reportUnusedCallResult=error`), `radon cc -n C` (`0` Grade-C+ functions), `lint-imports` (all 6 contracts), and `ast-grep test && ast-grep scan`.
- `HYPOTHESIS_PROFILE=ci uv run --frozen pytest -m property --fail-on-skip -q` and `uv run --frozen pytest --cov --fail-on-skip -q` pass with `>= 85%` branch coverage and zero skipped tests.
- All 7 adapter CI legs (`waza`, `skillspec`, `dspy`, `skillopt`, `evoskill`, `phoenix`, `mlflow`) pass isolated `--fail-on-skip` and 4-step SPDX license checks with zero `Elastic-2.0` pulls and zero Step-4 core/dev overrides.
- Staged Nix `checks.<system>.offline` builds and passes offline under an empty `$HOME`, verifying `nix/locked-versions.json` parity for both `packages` and `tools`, offline selfcheck, AST boundary check, and workspace tests.
- Read-only cross-repo parity checks of `skill-eval`, `skill-lint`, and `harness-eval` succeed against an external Agent Skill repository via `--repo-root` with zero hardcoded `artagon-scripts` paths inside `packages/*/src/`.
- `openspec validate --all --strict` passes with zero warnings or errors and `v0.2.0` release artifacts (wheels, `SHA256SUMS`, schema bundle) build cleanly.
