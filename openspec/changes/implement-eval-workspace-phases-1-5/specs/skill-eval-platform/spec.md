# Capability: skill-eval-platform

## ADDED Requirements

### Requirement: Isolated `skills-ref` Tier-0 Adapter and Layered Linter
`artagon_eval_skills.spec_adapter` SHALL be the sole module importing official `agentskills.io` `skills-ref`, returning frozen `SkillFrontmatter` (handling UTF-8 BOM and uppercase `SKILL.md`). `artagon_eval_skills.lint` SHALL compose Tier-0 (`spec_adapter`), Tier-1 (portability, hidden Unicode, `SecretVault` scan), and Tier-2 (multi-client manifest and `eval-v2` parity) into `EvalResult[LintReport]`.

#### Scenario: Detecting BOM-prefixed valid SKILL.md and invalid frontmatter
- GIVEN a skill directory containing a UTF-8 BOM-prefixed `SKILL.md` and a second directory missing `description`
- WHEN `skill-lint` executes Tier-0 through Tier-2 checks
- THEN the valid skill SHALL produce `Ok(SkillFrontmatter)` and the invalid skill SHALL return `Error(SchemaUsageError)` with redacted diagnostics on `stderr`.

### Requirement: Frozen `eval-v2` Contracts with Zero Import-Time Disk I/O
`artagon_eval_skills.contracts` (`suite`, `results`, `inventory`, `overlays`) SHALL validate `evals.json`, `trigger-evals.json`, `execution-evals.json`, promoted results, and optional target-repo inventory/rubric overlays using `FrozenModel` (`strict=True, extra="forbid"`) with zero disk reads at module import time.

#### Scenario: Failing closed on malformed target-repo overlay config
- GIVEN a target repository with an invalid `configs/skill_eval_inventory.json` containing unknown keys
- WHEN `contracts.overlays` loads target-repo overrides via `--repo-root`
- THEN it SHALL return `Error(SchemaUsageError)` (`exit 2`) rather than silently falling back to packaged defaults.

### Requirement: Deterministic PyYAML Suite Generator and Canonical Execution Fixtures
`artagon_eval_skills.generator.emitters` SHALL emit `eval.yaml`, `tasks/*.yaml`, `trigger_tests.yaml`, and `tasks.skillopt.json` using PyYAML (no hand-rolled YAML string builders) with `--check` drift verification. The single canonical 47-file execution fixture set SHALL reside in `packages/artagon-eval-skills/tests/fixtures/skill_eval_execution/`.

#### Scenario: Verifying deterministic generation parity in check mode
- GIVEN a repository whose generated skill eval files match canonical suite sources
- WHEN `skill-eval generate --check --repo-root <repo>` runs
- THEN it SHALL exit `0` with `mutations: "none"`, and any drifted file SHALL fail non-zero naming the drifted relative path.

### Requirement: Unified `skill-eval` Workflows, Holdout Quarantine Gate, and Promotion Patch
`artagon_eval_skills.workflows` (`lanes_build`, `lanes_run`, `lanes_score`, `gate`, `promote`, `report`, `purge`, `ntm_lab`, `native_compat`) and `cli/app.py` SHALL expose all `skill-eval` subcommands in a single Python process. Holdout `gate` SHALL enforce `TrainEvalCase`/`ValEvalCase`/`TestEvalCase` isolation and the `<= 3` ledger cap, and `promote` SHALL construct a `100644` `promotion.patch` outside `plugins/` only from a `GateAccepted` proof token.

#### Scenario: Refusing promotion when holdout gate rejects a candidate
- GIVEN a candidate whose paired holdout evaluation returns `GateRejected`
- WHEN `skill-eval promote` runs against that campaign
- THEN it SHALL exit `1` (`GateRejectedError`), log redacted diagnostics to `stderr`, and emit zero patch files.
