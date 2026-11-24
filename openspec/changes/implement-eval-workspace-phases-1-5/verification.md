# Verification: `implement-eval-workspace-phases-1-5`

| Check | Command or method | Result evidence path | Actual status |
| --- | --- | --- | --- |
| OpenSpec strict schema and delta validation | `openspec validate --all --strict` | `openspec/changes/implement-eval-workspace-phases-1-5/` | not run |
| Phase 1–5 static typing, lint, complexity, import boundaries, and structural rules | `uv run --frozen ruff check && uv run --frozen ruff format --check && uv run --frozen mypy && uv run --frozen basedpyright && uv run --frozen radon cc -n C packages/*/src && uv run --frozen lint-imports && ast-grep test --config sgconfig.yml && ast-grep scan --config sgconfig.yml` | `pyproject.toml` | not run |
| Hypothesis property suites (`ci` profile) and full workspace coverage (`>= 85%`) | `HYPOTHESIS_PROFILE=ci uv run --frozen pytest -m property --fail-on-skip -q && uv run --frozen pytest --cov --fail-on-skip -q` | `tests/conftest.py` | not run |
| ADR-0006 offline Nix check (`packages` + `tools` receipt parity, selfcheck, AST boundary, tests) | `uv run --frozen harness-eval-nix-check --offline` | `flake.nix`, `nix/locked-versions.json` | not run |
| 7-leg isolated adapter CI matrix (`waza`, `skillspec`, `dspy`, `skillopt`, `evoskill`, `phoenix`, `mlflow`) and 4-step SPDX license guard | `pytest --fail-on-skip` + `tests/packaging/test_license_guard.py` per adapter leg | `packages/` | not run |
| Read-only cross-repo parity and standalone plugin/APM lint | `skill-eval generate --check`, `skill-eval validate-results --all`, `skill-lint --skills-dir skills` | `skills/`, `apm.yml` | not run |
| `v0.2.0` release wheels, sdist, `SHA256SUMS`, and exported schema bundle | `.github/workflows/release.yml` | `pyproject.toml` | not run |

## Remaining gaps

- Phases 1–5 tasks (`1.1`–`5.5`) are seeded for execution and not yet implemented.
- Update this table with observed command outputs and repo-relative evidence paths as each phase completes; do not archive this change until all tasks are `[x]` and all required checks report `passed`.
