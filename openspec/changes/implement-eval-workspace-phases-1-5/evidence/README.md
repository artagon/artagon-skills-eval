# Evidence Index: `implement-eval-workspace-phases-1-5`

Use project-relative paths. For external sources, record a stable URL and access date.

| Claim or task | Source or proof path | What it supports | Actual status |
| --- | --- | --- | --- |
| Greenfield bootstrap provenance and extracted committed assets | `docs/PROVENANCE.md` | Clean `git archive` extraction from `artagon/artagon-scripts@4bc7df28c98704b344c91fce2c710d182a72144b` with canonical schemas, harnesses, skills, examples, ADRs, and `flake.lock`. | verified |
| Workspace root, 6 `import-linter` contracts, strict `mypy`/`basedpyright`/`ruff` gates | `pyproject.toml`, `uv.lock`, `sgconfig.yml`, `rules/python/` | Phase 0/1 workspace spine and mechanical quality gates configured on `main`. | verified |
| Initial core domain primitives, `spec_adapter.py`, and Hypothesis profile harness | `packages/artagon-eval-core/src/artagon_eval_core/domain/`, `packages/artagon-eval-skills/src/artagon_eval_skills/spec_adapter.py`, `tests/conftest.py` | Baseline `FrozenModel`, `Expression`, `RedactedStr`, `skills-ref` adapter, and `dev`/`ci`/`thorough` Hypothesis profiles present before Phase 1 completion. | verified |
| Root Nix flake clean-source guard and pinned `nixos-26.05` receipt | `flake.nix`, `flake.lock`, `nix/locked-versions.json` | Pinned `nixos-26.05` rev `c56a87d8e41ce69bd2af57eb35dcc117a9dfca33`, ADR-0006 `lib.fileset` filter, and eval-time forbidden-file guard seeded. | verified |
| Phase 1 completion (`1.1`–`1.5`: full core domain, ports, runtime, plugins, ADR-0006 staging & SPDX/version-bounds tests) | `packages/artagon-eval-core/src/`, `tests/packaging/` | Full FCIS core, `O_NOFOLLOW` host stager, AST boundary check, and `checks.<system>.offline` pass. | not checked |
| Phase 2 completion (`2.1`–`2.5`: 4-CLI decoders, multiplexers, DuckDB store, hot-path shims, `harness-eval` CLI, external repo overlay) | `packages/artagon-eval-core/src/artagon_eval_core/{shell,store,shims,cli}/`, `tests/integration/` | Full harness runtime, `<= 5ms` `-P -s -m` shims, and zero-config external repo targeting. | not checked |
| Phase 3 completion (`3.1`–`3.5`: `artagon-eval-skills` contracts, Tier-0/1/2 linter, PyYAML generator, unified `skill-eval` workflows & parity) | `packages/artagon-eval-skills/src/`, `packages/artagon-eval-skills/tests/fixtures/skill_eval_execution/` | Complete skill-eval platform and read-only cross-repo parity against external Agent Skill suites. | not checked |
| Phase 4 completion (`4.1`–`4.3`: `waza`, `skillspec` adapters & standalone multi-CLI plugin/APM manifests) | `packages/artagon-eval-waza/`, `packages/artagon-eval-skillspec/`, `skills/`, `apm.yml` | Independent benchmark/validation adapters and standalone plugin/APM packaging. | not checked |
| Phase 5 completion (`5.1`–`5.5`: `dspy`, `skillopt`, `evoskill`, `observability` adapters & `v0.2.0` release workflow) | `packages/artagon-eval-{dspy,skillopt,evoskill,observability}/`, `.github/workflows/release.yml` | All 7 isolated adapter CI legs passing `--fail-on-skip`, zero `Elastic-2.0`, and verified `v0.2.0` release bundle. | not checked |

Record observed results only. Keep failed, pending, and not-run checks explicit; do not infer success from a planned command.
