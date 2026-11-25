# Project Context (`artagon-skills-eval`)

> **Canonical agent instructions:** Repository-wide engineering contracts, strict typing rules, Hypothesis property-testing policy, and verification commands live in [`AGENTS.md`](../AGENTS.md) (`CLAUDE.md` and `AGENT.md` symlink to it). **Read `AGENTS.md` first.** This file adds OpenSpec context, directory layout, and active change sequencing without duplicating root rules.

## Purpose

`artagon-skills-eval` is a standalone, subscription-first Python and Nix evaluation platform for Agent Skills and multi-CLI coding harnesses (`claude`, `codex`, `agy`, `copilot`). It provides a functional core evaluation engine, official `agentskills.io` `skills-ref` linting, 4-layer trace storage (DuckDB/Parquet + OTLP), ADR-0012 hot-path shims, and six lazily-loaded Pluggy integration adapters (`waza`, `dspy`, `skillopt`, `evoskill`, `skillspec`, `observability`).

See [`README.md`](../README.md) for quickstarts, [`ABOUT.md`](../ABOUT.md) for design guarantees, [`docs/PROVENANCE.md`](../docs/PROVENANCE.md) for extraction lineage, and [`docs/adr/`](../docs/adr/) for Architecture Decision Records (`0005`–`0007`, `0009`–`0012`, `0015`–`0016`).

## Technology Stack

- **Runtime & Packaging:** Python `3.12+` / `3.13`, `uv` workspace ([`pyproject.toml`](../pyproject.toml), [`uv.lock`](../uv.lock)), Hatchling wheel builds.
- **Type & FP Stack:** Strict frozen Pydantic v2 (`FrozenModel`), `Expression 6.0.1` (`expression[pydantic]`), `rpds-py` (`PersistentMap`, `PersistentSet`), capability-sealed `RedactedStr`.
- **Specifications & Plugins:** Official `agentskills.io` `skills-ref` (isolated in `artagon_eval_skills.spec_adapter`), `pluggy` + lazy `importlib.metadata` entry points.
- **Telemetry & Storage:** `structlog` + `detect-secrets` (`SecretVault`), DuckDB, PyArrow Parquet, OTLP protobuf/JSON, RFC 8785 (`rfc8785`).
- **Hermetic Packaging:** Root Nix flake ([`flake.nix`](../flake.nix), [`flake.lock`](../flake.lock), [`nix/locked-versions.json`](../nix/locked-versions.json)) pinned to `nixos-26.05` with ADR-0006 clean-source filtering and `O_NOFOLLOW` host staging.
- **Verification & Governance:** `pytest`, Hypothesis (`dev`/`ci`/`thorough`), `ruff`, `mypy --strict`, `basedpyright --strict`, `radon`, `import-linter`, `ast-grep` ([`sgconfig.yml`](../sgconfig.yml)), and OpenSpec `2.1.0` (`spec-driven-evidence` schema).

## OpenSpec Layout

```text
openspec/
├── config.yaml                          # Active schema (spec-driven-evidence), context, and artifact rules
├── project.md                           # This file: project context and change sequencing
├── AGENTS.md                            # OpenSpec-specific editing and validation rules
├── schemas/
│   └── spec-driven-evidence/            # Local workflow schema and artifact templates
├── specs/                               # Promoted capability specifications (populated on archive)
└── changes/
    └── <change-id>/                     # One directory per scoped change
        ├── .openspec.yaml               # Per-change schema binding
        ├── proposal.md                  # Problem, scope, capabilities, success criteria
        ├── specs/<capability>/spec.md   # Normative ADDED/MODIFIED/REMOVED requirements + scenarios
        ├── design.md                    # Technical approach, module layout, decisions, risks
        ├── tasks.md                     # Phased checklist with Proof and Status lines
        ├── evidence/README.md           # Observed evidence index (repo-relative paths only)
        ├── review.md                    # Review findings, dispositions, and review scope
        └── verification.md              # Gate execution results and remaining gaps
```

## OpenSpec Conventions

- Use the `spec-driven-evidence` schema defined in [`schemas/spec-driven-evidence/schema.yaml`](schemas/spec-driven-evidence/schema.yaml).
- Write normative requirements with `SHALL` or `MUST`, keep each requirement statement concise (under 450 characters), and attach at least one `#### Scenario:` (`GIVEN`/`WHEN`/`THEN`).
- Pair pure domain and boundary requirements with Hypothesis `@pytest.mark.property` coverage (`HYPOTHESIS_PROFILE=ci`).
- Run `openspec validate --all --strict` before handoff or commit.
- Public repository hygiene: use repository-relative paths only; never record machine-local home paths, corporate domains, personal emails, local file-scheme URIs, or secrets.

## Change Sequencing

Run `openspec list` for live change progress.

| Tier | Change ID | Scope | Dependencies / Notes |
| --- | --- | --- | --- |
| Tier 1 (Active) | `implement-eval-workspace-phases-1-5` | Complete Phases 1–5 of the standalone workspace (`artagon-eval-core`, `artagon-eval-skills`, all 6 lazy adapters, plugin/APM manifests, and `v0.2.0` release packaging). | Builds on the already-bootstrapped Phase 0/1 workspace spine (`pyproject.toml`, `flake.nix`, core domain primitives, `spec_adapter.py`, and Hypothesis harness). |
| External Follow-Up | Consumer cutover (Phases 6–7 in `artagon/artagon-scripts`) | Wire thin repo-scoped delegator launchers and retire legacy monorepo eval code after `v0.2.0` ships. | Tracked in `artagon/artagon-scripts` once `implement-eval-workspace-phases-1-5` completes and cuts `v0.2.0`. |
