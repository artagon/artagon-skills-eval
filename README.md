# `artagon-skills-eval`

Subscription-first, multi-CLI Agent Skill and harness evaluation suite, static linter, 4-layer trace store, and pluggable optimizer adapters.

## Quickstart & Verification

Install the `uv` workspace and run every quality gate:

```bash
uv sync --group dev
openspec validate --all --strict
uv run --frozen pytest -q
uv run --frozen pytest -m property --fail-on-skip -q
uv run --frozen ruff check
uv run --frozen mypy
uv run --frozen basedpyright
uv run --frozen radon cc -n C packages/*/src
uv run --frozen lint-imports
ast-grep test --config sgconfig.yml && ast-grep scan --config sgconfig.yml
```

Run Hypothesis property-based suites with explicit profiles registered in [tests/conftest.py](tests/conftest.py) (`dev`: 50 examples local default; `ci`: 100 examples deterministic `derandomize=True`; `thorough`: 1000 examples pre-release/stress; all `deadline=None`):

```bash
HYPOTHESIS_PROFILE=ci uv run --frozen pytest -m property --fail-on-skip -q
HYPOTHESIS_PROFILE=thorough uv run --frozen pytest -m property --fail-on-skip -q
```

## Workspace Packages

| Package | Distribution | Responsibility |
| --- | --- | --- |
| Root umbrella | `artagon-skills-eval` | Unified CLI entrypoints (`harness-eval`, `skill-eval`, `skill-lint`, `skillopt-runner`, `harness-eval-nix-check`) and optional adapter extras |
| [packages/artagon-eval-core](packages/artagon-eval-core/pyproject.toml) | `artagon-eval-core` | Pure frozen domain models (`FrozenModel`, `Expression`, `rpds-py`, `RedactedStr`), typed effect `Protocol` ports, `SecretVault`, `structlog`, Pluggy hookspecs, ADR-0012 hot-path shims, and canonical packaged data |
| [packages/artagon-eval-skills](packages/artagon-eval-skills/pyproject.toml) | `artagon-eval-skills` | Official `agentskills.io` `skills-ref` Tier-0 adapter, skill contracts, `skill-eval`, and `skill-lint` |
| [packages/artagon-eval-waza](packages/artagon-eval-waza/pyproject.toml) | `artagon-eval-waza` | Lazy Pluggy benchmark/sink adapter for Waza |
| [packages/artagon-eval-dspy](packages/artagon-eval-dspy/pyproject.toml) | `artagon-eval-dspy` | Lazy Pluggy optimizer adapter for DSPy / GEPA / pyDSP |
| [packages/artagon-eval-skillopt](packages/artagon-eval-skillopt/pyproject.toml) | `artagon-eval-skillopt` | Lazy Pluggy optimizer adapter for SkillOpt (`0.2.0`) |
| [packages/artagon-eval-evoskill](packages/artagon-eval-evoskill/pyproject.toml) | `artagon-eval-evoskill` | Lazy Pluggy optimizer adapter for EvoSkill |
| [packages/artagon-eval-skillspec](packages/artagon-eval-skillspec/pyproject.toml) | `artagon-eval-skillspec` | Lazy Pluggy benchmark/optimizer adapter for SkillSpec |
| [packages/artagon-eval-observability](packages/artagon-eval-observability/pyproject.toml) | `artagon-eval-observability` | Lazy Pluggy Apache-2.0 Phoenix OTel and MLflow 3 telemetry sink adapter |

## CLI Entrypoints

```bash
uv run harness-eval --help
uv run skill-eval --help
uv run skill-lint --help
uv run skillopt-runner --help
uv run harness-eval-nix-check --help
```

## Nix Environment

Pinned against `nixos-26.05` (`flake.lock`) with exact versions recorded in [nix/locked-versions.json](nix/locked-versions.json) and ADR-0006 clean-source filtering (`lib.fileset.toSource`) + eval-time forbidden-file guards in [flake.nix](flake.nix):

- `devShells.<system>.default`: isolated eval shell with metered billing env scrubbing and `PYTHONNOUSERSITE=1`
- `devShells.<system>.dev`: contributor toolchain (`ruff`, `mypy`, `basedpyright`, `radon`, `uv`, `ast-grep`)
- `devShells.<system>.skillopt`: optional pinned `skillopt 0.2.0` closure
- `checks.<system>.offline`: pure offline verification under an empty `$HOME`

## OpenSpec Workflow

Architectural changes are governed with OpenSpec `2.1.0` using the [`spec-driven-evidence`](openspec/schemas/spec-driven-evidence/schema.yaml) schema ([openspec/config.yaml](openspec/config.yaml)):

```bash
openspec list
openspec status --change implement-eval-workspace-phases-1-5
openspec validate --all --strict
```

- [openspec/project.md](openspec/project.md) — OpenSpec project context and change sequencing
- [openspec/AGENTS.md](openspec/AGENTS.md) — Spec editing rules and strict validation commands
- [openspec/changes/implement-eval-workspace-phases-1-5/proposal.md](openspec/changes/implement-eval-workspace-phases-1-5/proposal.md) — Seeded Phases 1–5 implementation change

## Documentation & Governance

- [ABOUT.md](ABOUT.md) — Executive overview, architecture, and security guarantees
- [AGENTS.md](AGENTS.md) — Engineering contract, type system, property-based testing policy, and verification gates
- [openspec/project.md](openspec/project.md) — OpenSpec `spec-driven-evidence` context and roadmap
- [docs/PROVENANCE.md](docs/PROVENANCE.md) — Origin commit SHA and clean extraction lineage
- [docs/adr/](docs/adr/) — Architecture Decision Records (`0005`–`0007`, `0009`–`0012`, `0015`–`0016`)
- [schemas/README.md](schemas/README.md) — Single canonical JSON schema location
- [skills/](skills/) — Portable Agent Skills (`harness-eval`, `harness-eval-author`, `harness-eval-trace`)
- [examples/](examples/) — Portable multi-CLI canary protocol and RFC 8785 MCP cassettes
