# Design: Standalone `artagon-skills-eval` Workspace (Phases 1–5)

## Context

`artagon-skills-eval` was bootstrapped via clean greenfield `git init -b main` from committed reference assets in `artagon/artagon-scripts@4bc7df28c98704b344c91fce2c710d182a72144b` (`docs/PROVENANCE.md`).

Already present on `main` from Phase 0 and initial Phase 1 bootstrap:
- Root `pyproject.toml` (`[tool.uv.workspace]`, umbrella `artagon-skills-eval`, strict `ruff`, `mypy`, `basedpyright`, `radon`, 6 `import-linter` contracts, `pytest`), `uv.lock`, `sgconfig.yml`, and 5 `rules/python/*.yml` ast-grep rules + `rule-tests/`.
- Root `flake.nix`, `flake.lock` (`nixos-26.05` rev `c56a87d8e41ce69bd2af57eb35dcc117a9dfca33`), and `nix/locked-versions.json`.
- `packages/artagon-eval-core/` foundation: `domain/{types,fp,primitives,errors}.py`, `ports/effects.py`, `runtime/{redact,logging}.py`, `plugins/contracts.py`, `shims/{wire,scrub}.py`, `packaging/nix_check.py`, `cli/{app,skillopt_proxy}.py`, and single canonical `data/` (10 JSON schemas, 6 harness YAMLs, `providers.json`, `keychain-services.json`).
- `packages/artagon-eval-skills/` foundation: `spec_adapter.py` (`skills-ref==0.1.1`), `cli/{app,lint}.py`, and empty subpackage skeletons (`contracts/`, `lint/`, `generator/`, `workflows/`, `data/`).
- Six adapter package stubs (`packages/artagon-eval-{waza,dspy,skillopt,evoskill,skillspec,observability}/`) with `plugin.py` smoke entry points.
- Hypothesis profile harness (`tests/conftest.py`, `packages/artagon-eval-core/tests/strategies.py`), core/skills property suites, and negative compile-time typing suite (`tests/typing/test_negative_typing.py`).

Phases 1–5 complete the full runtime, skills platform, six adapters, standalone plugin/APM packaging, and `v0.2.0` release pipeline inside `artagon-skills-eval` without mutating any consumer repository.

## Approach

### 1. Functional Core / Imperative Shell (FCIS) & Strict Typestate Spine

```text
CLI (Typer ctx.obj, zero globals)
  -> Shell (5-CLI decoders, multiplexers, custody, cassette, OTLP, DuckDB store)
    -> Runtime (structlog, SecretVault, JCS, CampaignAbortLatch, ChildEnvBuilder, pins, patch, curation)
      -> Plugins (Pluggy hookspecs + lazy importlib.metadata PluginRegistry)
        -> Ports (typed Effect Protocols returning EvalResult[T])
          -> Domain (100% pure FrozenModel + Expression 6.0.1 + rpds-py + RedactedStr)

Hot-Path Shims (`artagon_eval_core.shims.*`): isolated `-P -s -m` stdlib (+ optional msgspec) ONLY.
```

All 6 boundary contracts in `pyproject.toml` (`[tool.importlinter]`) are enforced in CI via `lint-imports` and mirrored inside Nix `checks.<system>.offline` by a zero-dependency AST validator (`artagon_eval_core.packaging.boundary_check`).

### 2. Module Decomposition Targets (Every Module `<= 300` LOC, `CC <= 8`)

1. **Phase 1 (`packages/artagon-eval-core/`):**
   - Complete pure `domain/`: `billing.py` (single canonical `METERED_BILLING_ENV_VARS`), `splits.py`, `protocol.py` (`DraftProtocol -> ResolvedProtocol -> FrozenManifest`), `auth.py` (`SubscriptionAuth | ApiKeyAuth`, `FiniteBudget`, MCP server union), `capability.py`, `model_spec.py`, `schedule.py` (ABBA/BAAB/RCB), `stats.py` (ITT lift, paired bootstrap, permutation, Holm-Bonferroni), `outcome.py`, `judge_policy.py`, `trace_models.py`, `assertions.py`, `planner.py`.
   - Split typed `ports/`: `subprocess.py`, `filesystem.py`, `custody.py`, `keyring.py`, `telemetry.py`, `scrubber.py`.
   - Complete `runtime/`: `jcs.py`, `latch.py`, `child_env.py`, `proposer.py`, `pins.py`, `patch.py`, `curation.py`.
   - Complete `plugins/`: `hookspecs.py`, `registry.py`, `hooks_compiler.py`.
   - Complete `packaging/`: `staging.py` (ADR-0006 `O_NOFOLLOW` `0700` stager), `selfcheck.py`, `boundary_check.py`, plus `tests/packaging/{test_version_bounds,test_license_guard,test_nix_staging}.py`.
2. **Phase 2 (`packages/artagon-eval-core/` + `scripts/`):**
   - `shell/transcript/{claude,codex,agy,copilot,kimi,otel_reducer,fusion}.py`
   - `shell/multiplexers/{ntm,herdr,cao,hcom}.py`
   - `shell/{catalog_loader,model_resolver,workspace,custody_fs,materializer,keyring,cassette,otlp_sink,judge_runner,trial_executor}.py`
   - `store/{parquet_writer,duckdb_query,sql_guard,otlp_export}.py`
   - `shims/{trampoline,hook_sink}.py` (preserving `-P -s -m` `<= 5ms` contract)
   - `cli/{cmd_auth,cmd_campaign,cmd_trace,cmd_ops}.py` + `scripts/{harness-eval,harness-eval-nix-check}.py` (Python 3.9 AST-parseable stdlib launchers with billing-var parity tests)
   - External targeting (`--repo-root`, `--config-dir`, `--skills-dir`, `--work-dir`) with deterministic 4-layer `PersistentMap` overlay precedence (Packaged Defaults -> Target Repo Overlays -> Explicit CLI Flags -> Operator Local Model Caches) verified in `tests/integration/test_external_repo_targeting.py`.
3. **Phase 3 (`packages/artagon-eval-skills/`):**
   - `contracts/{suite,results,inventory,overlays}.py` (zero import-time disk reads)
   - `lint/{portability,security,plugin_parity,runner}.py` composing `spec_adapter.py`
   - `generator/emitters.py` (PyYAML emitters + `--check`)
   - `workflows/{lanes_build,lanes_run,lanes_score,gate,promote,report,purge,ntm_lab,native_compat}.py` (fixing legacy `lanes_score` overwrite bug and absorbing unique NTM lab analysis workflows)
   - Unified `cli/{app,lint}.py` (`skill-eval` and `skill-lint`) + canonical 47-file fixtures in `packages/artagon-eval-skills/tests/fixtures/skill_eval_execution/`.
4. **Phases 4–5 (Six Independent Adapters + Packaging + Release):**
   - `packages/artagon-eval-waza/`: `compiler/{graders,tasks,manifest}.py`, `exporter/outcome.py`, `runner/{mock,copilot_sdk,harness}.py`, `waza_pin.json`, `plugin.py`.
   - `packages/artagon-eval-skillspec/`: `pin_runner.py`, `phase1_search.py`, `skillspec_pin.json`, `plugin.py`.
   - `packages/artagon-eval-dspy/`: `lm_engine.py`, `gepa_runner.py`, `dspy_module.py`, `quarantine.py` (zero mutable dict leaks), `plugin.py`.
   - `packages/artagon-eval-skillopt/`: `gateway.py`, `patch_merge.py`, `harvest.py`, `isolated_main.py` (`python3 -I`), `cli.py`, `skillopt_pin.json`, `plugin.py`.
   - `packages/artagon-eval-evoskill/`: `loader.py` (scoped dist loader, zero import-time `sys.meta_path` mutation), `solver.py`, `evolver.py` (Seatbelt/bwrap kernel sandbox with `O_NOFOLLOW` read-back), `plugin.py`.
   - `packages/artagon-eval-observability/`: `phoenix_sink.py` (Apache-2.0 `arize-phoenix-otel` + `arize-phoenix-client` + `openinference-semantic-conventions` only), `mlflow_sink.py` (`mlflow-tracing` + optional `mlflow-skinny`), `offline_scorer.py`, `plugin.py`.
   - Standalone manifests (`plugin.json`, `.{claude,codex,copilot,kimi}-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `kimi.plugin.json`, `apm.yml`, `apm.lock.yaml`, `EXTENSION.md`) and `.github/workflows/release.yml` for `v0.2.0`.

## Decisions

| ID | Decision | Rationale & Rejected Alternatives |
| --- | --- | --- |
| D1 | `Expression 6.0.1` (`expression[pydantic]`, MIT) + `rpds-py` | Native Pydantic v2 tagged-union schemas and zero-plugin `basedpyright --strict` narrowing. Rejected `returns` (mypy-plugin conflict with `basedpyright`, no Pydantic v2 union support) and hand-rolled monads. |
| D2 | Keep `typer` for CLI entrypoints | Locked in `nixos-26.05`, Click parity with `skills-ref`, minimal migration churn vs `cyclopts`. |
| D3 | Absorb `skillopt 0.2.0` Nix output + NTM lab workflows | Eliminates duplicate Nix flake and unlinted parallel scripts while keeping `skillopt` out of core `checks.offline`. |
| D4 | Root `flake.nix` Path A (`buildPythonPackage` + ADR-0006 `lib.fileset` + `O_NOFOLLOW` stager) | Immediate offline verification against pinned `nixos-26.05` (`structlog>=25.5.0`, `rpds-py>=0.22.0`); `uv2nix` deferred to Phase 8. |
| D5 | Defer `artagon-eval-pydantic-evals` and `sqlglot` to Phase 8 | Keeps Phases 1–5 focused on stabilizing core, skills, and the 6 existing adapters before adding new dependencies. |
| D6 | Pin PyPI `skills-ref==0.1.1` behind `artagon_eval_skills.spec_adapter` | Official `agentskills.io` Tier-0 spec parser/validator; isolated behind one adapter module + local `typings/skills_ref/*.pyi` stubs. |
| D7 | Clean greenfield repo + single canonical `data/schemas/` | Eliminates ADR-0012 `git subtree split` policing, triple-mirrored schemas, dual-mirrored fixtures, and monorepo `apm.exports.json` hash churn. |

## Risks

- **Dual type-checker ergonomics (`mypy --strict` + `basedpyright --strict`):** Long unannotated `expression.pipe(...)` chains can degrade inference in `mypy`. Mitigation: mandate dot-chaining (`.map()`, `.bind()`, `.map_error()`, `.or_else_with()`) and exhaustive `match`/`assert_never`, guarded by `tests/typing/test_negative_typing.py`.
- **Nix vs PyPI version drift:** Raising a lower bound in `pyproject.toml` above `nix/locked-versions.json` (e.g. `structlog` `25.5.0` or `rpds-py` `0.30.0`) breaks offline Nix builds. Mitigation: enforce `tests/packaging/test_version_bounds.py` in CI and assert both `packages` and `tools` in `checks.<system>.offline`.
- **Optional adapter license contamination:** Transitive pulls of `arize-phoenix` (`Elastic-2.0`) would violate the repository license policy. Mitigation: pin Apache-2.0 client/OTel packages only and gate every adapter CI leg with `tests/packaging/test_license_guard.py` and `--fail-on-skip`.
- **Symlink/TOCTOU leakage into `/nix/store/` or promotion patches:** Mitigation: keep canonical schemas as regular files inside `artagon_eval_core/data/schemas/` (zero symlinks), enforce ADR-0006 `lib.fileset` + eval-time forbidden-file guard + `O_NOFOLLOW` host staging, and verify `100644` patch confinement outside `plugins/`.
