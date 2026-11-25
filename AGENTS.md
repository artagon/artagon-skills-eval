# Agent Instructions (`artagon-skills-eval`)

## Project Shape & Workspace Topology

`artagon-skills-eval` is a standalone Python `3.12+` / `3.13` `uv` workspace and Nix flake (`nixos-26.05`) for subscription-first multi-CLI skill and harness evaluation across Claude, Codex, Antigravity, and Copilot. See [README.md](README.md) for operator quickstarts and CLI usage, [ABOUT.md](ABOUT.md) for executive guarantees and architecture, and [docs/PROVENANCE.md](docs/PROVENANCE.md) for origin lineage.

| Path | Ownership & Role |
| --- | --- |
| [pyproject.toml](pyproject.toml) | `[tool.uv.workspace]` root (`members = ["packages/*"]`), umbrella package `artagon-skills-eval`, and single-source static/test gate configuration. |
| [packages/artagon-eval-core](packages/artagon-eval-core) | Pure FCIS `domain/` models, `Expression` FP primitives, typed Effect `ports/`, `runtime/` (`structlog` + `SecretVault`), `Pluggy` hookspecs & lazy registry, DuckDB/Parquet `store/`, ADR-0012 `-P -s -m` hot-path `shims/`, canonical `data/` schemas/catalogs, and `harness-eval` CLI. |
| [packages/artagon-eval-skills](packages/artagon-eval-skills) | `agentskills.io` `skills-ref` Tier-0/1/2 linter (`spec_adapter.py`), `eval-v2` contracts, generator, lanes/gate/promote workflows, and `skill-eval` / `skill-lint` CLIs. |
| `packages/artagon-eval-{waza,dspy,skillopt,evoskill,skillspec,observability}` | Six decoupled, lazily-loaded `Pluggy` integration adapters (`importlib.metadata` entry points). Zero cross-adapter imports; missing adapters fail closed with `exit 69`. |
| [flake.nix](flake.nix) | Root Nix flake (`nixos-26.05`) with ADR-0006 `lib.fileset` clean-source filter, eval-time forbidden-file guard, `devShells`, and offline checks. |
| [sgconfig.yml](sgconfig.yml) & [rules/python](rules/python) | Structural `ast-grep` lint rules and snapshot tests (`rule-tests/`). |
| [openspec](openspec/project.md) | OpenSpec `2.1.0` configuration (`spec-driven-evidence` schema), promoted specs (`openspec/specs/`), and active changes (`openspec/changes/`). |
| [skills](skills) & [apm.yml](apm.yml) | Exported portable evaluation Agent Skills (`harness-eval`, `harness-eval-author`, `harness-eval-trace`). |
| `.agents/skills/` & `.claude/skills` | Project-local Python (`30`) and Shell (`8`) engineering skills wired via relative symlink `.claude/skills -> ../.agents/skills`. Excluded from the ADR-0006 Nix public source allowlist. |

## First Checks

- Run `git status --short --branch` before editing; preserve unrelated local changes.
- Run `openspec list` before planning or implementing behavior changes; read [openspec/project.md](openspec/project.md) and [openspec/AGENTS.md](openspec/AGENTS.md) when touching specifications or change artifacts.
- Never commit `.env`, credentials, tokens, scratch runs, holdout fixtures, machine-local home paths, or local file-scheme URIs.
- Use repository-relative markdown links only in docs and guidance files.
- Prefer `ast-grep` for structural searches and enforce structural invariants via [sgconfig.yml](sgconfig.yml).

## Python Style & Type System Contract

This repository enforces a strict functional, immutable, typestate-driven Python `3.12+` style. Whenever a general Python skill example shows mutable `dict`/`list` records or bare exceptions, **this contract takes precedence**.

### 1. Strict Frozen Domain Models (`FrozenModel`)

- Every domain record MUST inherit `FrozenModel` (`ConfigDict(frozen=True, extra="forbid", strict=True, validate_default=True, populate_by_name=True, arbitrary_types_allowed=False)`).
- `strict=True` bans silent coercions (`bool`-as-`int`, `str`-as-`int`, `float`-as-`int`); `extra="forbid"` fails closed on unknown keys.
- **Never** call `model_copy(update=...)` on domain models because it bypasses field and `@model_validator` hooks. Evolve immutable instances only through validated fluent `.with_*()` methods backed by `_evolve(...)` (re-running `model_validate` under `strict=True`).

### 2. Immutable Collections Only in `domain/` (Zero `Any`)

- Allowed domain containers: `tuple[T, ...]` (ordered sequences), `frozenset[T]` (membership sets), `PersistentMap[K, V]` (`rpds.HashTrieMap` via `rpds-py`), `PersistentSet[T]` (`rpds.HashTrieSet`), and `expression.collections.{Block, Map}`.
- Represent arbitrary JSON payloads with closed recursive `JsonValue` (`JsonScalar | tuple[JsonValue, ...] | PersistentMap[str, JsonValue]`), never `dict[str, Any]`.
- **Forbidden** in `domain/` and on any `FrozenModel` field: `list`, `dict`, `set`, `MutableMapping`, `MutableSequence`, `dict[str, Any]`, `Any`, and `cast(...)` escape hatches. Enforced by `basedpyright --strict` (`reportAny = "error"`, `reportExplicitAny = "error"`), `mypy --strict` (`disallow_any_explicit = true` on `domain`), and `rules/python/no-dict-str-any-in-domain.yml`.

### 3. Third-Party Functional Algebra (Do Not Hand-Roll Monads)

- Use **`Expression` (`expression[pydantic] >= 6.0.1, < 7`)** as the sole FP primitive layer. Never write custom `Option`, `Result`, or `Either` combinator classes.
- Use:
  - `Option[T]` (`Some[T] | Nothing`) for optional domain values;
  - `Result[T, E]` (`Ok[T] | Error[E]`, aliased as `EvalResult[T] = Result[T, EvalError]`) for fallible operations;
  - `@final @case` `TaggedUnion` for symmetric `Either[L, R]` and closed multi-case domain ADTs;
  - `NullableOption[T]` for Draft 2020-12 JSON wire fields (`null`/omitted on disk, `Option[T]` in Python).
- **Dual-checker composition rule:** Prefer method dot-chaining (`.map()`, `.bind()`, `.map_error()`, `.or_else_with()`) and exhaustive `match`/`case` ending in `typing.assert_never(...)` over long unannotated `pipe(...)` chains so code type-checks identically under **both** `basedpyright --strict` and `mypy --strict`.

### 4. Typestates & Making Illegal States Unrepresentable

Encode lifecycle, billing, split, and redaction invariants in the type system so violations fail at compile time or the parse boundary:

- **Manifest lifecycle:** `DraftProtocol -> ResolvedProtocol -> FrozenManifest`. `FrozenManifest` does not define `.with_arm_override()`.
- **Auth & budget:** Discriminated union `SubscriptionAuth | ApiKeyAuth`. `SubscriptionAuth` forbids `api_key_ref` and `provider_override` (`extra="forbid"`); `ApiKeyAuth` requires `FiniteBudget` (`max_cost_usd` or `max_tokens > 0`).
- **Holdout quarantine:** Separate `TrainEvalCase`, `ValEvalCase`, and `TestEvalCase`. Optimizers accept only `QuarantinedSuiteSplit` / `QuarantinedOptimizerCorpus` (never `TestEvalCase`) and emit receipts with `test_executions: Literal[0] = 0`.
- **Gate & promotion:** Closed `GateAccepted | GateRejected | GateBlocked` ADT. `PromotionPatch` constructs only from a `GateAccepted` proof token.
- **Capability-sealed `RedactedStr`:** Minted exclusively by `SecretScrubberPort.scrub()` / `SecretVault.scrub()` (or compile-time string constants via `static_redacted_literal()`, enforced by `rules/python/static-redacted-literal-const-only.yml`). Raw `str` is a compile-time and runtime error on `EvalError`, `ErrEnvelope`, traces, and verdicts.
- **Nominal primitives:** Use constrained `Annotated` types and `NewType` IDs (`CampaignId`, `TrialId`, `ArmId`, `TaskId`, `SafeId`, `SkillId`, `Sha256Hex`, `RelativeRepoPath`, `ConfinedScratchPath`).

### 5. Zero Silent Failures

- Pure domain logic and typed Effect `Protocol` ports return `EvalResult[T]`; never raise untyped exceptions across layer boundaries. Catch stdlib or third-party exceptions at thin `shell/` or adapter edges and map immediately to the closed 11-variant `EvalError` ADT (`GateRejectedError`, `SchemaUsageError`, `CredentialUnavailableError`, `BillingGuardError`, `IsolationTamperError`, `VerifierCassetteError`, `QuotaCensoredError`, `MultiplexerError`, `CliUsageError`, `SplitDataError`, `AdapterUnavailableError`).
- Project `EvalError` 1-to-1 onto `NormativeExitCode` (`0, 1, 2..8, 64, 65, 69`) via exhaustive `match`/`assert_never`.
- Ignoring an `EvalResult[T]` is a compile error (`basedpyright` `reportUnusedCallResult = "error"`).
- Blind or empty `except` blocks and `contextlib.suppress(Exception)` are banned (`ruff` `BLE`/`TRY` and `rules/python/no-silent-except.yml`).
- Every CLI failure MUST log `RedactedStr` diagnostics (`reason_code`, `exit_code`, `error`, `log_paths`) to `stderr` via `structlog` with the mandatory `SecretVault` processor so redirecting `stdout >/dev/null` never hides errors. Never swallow subprocess `stdout` or `stderr`. Never call `sys.exit()` inside `domain/` or `shell/`.

### 6. Functional Core / Imperative Shell (FCIS), Complexity & Modularity

- Pure `domain/` MUST have zero I/O, CLI, database, network, or subprocess imports and zero import-time disk reads.
- Route all side effects through typed `Protocol` ports (`artagon_eval_core.ports`) with deterministic in-memory fakes for tests.
- Ban mutable module-level globals and singletons (inject `AppContext` via Typer `ctx.obj`; enforced by `rules/python/no-mutable-module-globals.yml`).
- Ban `sys.path.insert` and global `sys.meta_path` mutation (`rules/python/no-sys-path-mutation.yml`).
- Keep ADR-0012 hot-path shims (`artagon_eval_core.shims.*`, invoked with `-P -s -m`) restricted to stdlib plus optional `msgspec`.
- Enforce all 6 `import-linter` contracts in [pyproject.toml](pyproject.toml): FCIS layers, pure domain, hot-path shims, core/adapter isolation, adapter mutual independence, and `skills-ref` isolation.
- **Formatting & complexity budgets:** `from __future__ import annotations`, PEP 695 `type` aliases and generics, `line-length = 100`, target `<= 300 LOC` per module, target cyclomatic complexity `CC <= 8` (`ruff` `C90` `max-complexity = 8`, hard CI cap `<= 10`, zero Grade-C+ functions under `radon cc -n C`).

### 7. Prior-Art First (Do Not Reinvent)

- **`agentskills.io` `skills-ref`:** Sole Tier-0 `SKILL.md` parser/validator, isolated strictly inside `artagon_eval_skills.spec_adapter`.
- **`Expression` + `rpds-py`:** Algebraic FP types and persistent hash-trie collections.
- **`pluggy` + lazy `importlib.metadata`:** Decoupled adapter discovery under `packages/artagon-eval-*` (zero cross-adapter imports, zero startup import cost).
- **`structlog` + `detect-secrets` (`SecretVault`):** Scrubbed structured diagnostics.
- **`pytest` + `hypothesis` (`dev`/`ci`/`thorough` profiles):** Unit, property, and negative compile-time typing (`tests/typing/`) verification.
- **`ruff`, `mypy --strict`, `basedpyright --strict`, `radon`, `import-linter`, `ast-grep`:** Mandatory mechanical gates.

### 8. Security & Subscription-Only Invariants

- Never weaken metered-billing env/config guards, holdout split quarantine, `O_NOFOLLOW` confinement and ADR-0006 clean-source staging, read-only method-only keyring isolation, or `SecretVault` scrubbing.
- Never print, log, or commit secret values. Verify credentials by key name or exit status only.

### 9. Property-Based Testing (Hypothesis)

- **Default for pure & boundary invariants:** Property-based testing with Hypothesis (`@pytest.mark.property`) is the **default** for all pure domain functions, algebraic types (`Option`, `Result`, `Either`, `NullableOption`), parsers and validators (`RelativeRepoPath`, `SkillId`, `ModelId`, `parse_task_split`, `ConfinedScratchPath`), redaction and security boundaries (`SecretVault`, `RedactedStr`), frozen model evolution (`_evolve()` / `.with_*()`), and `skills-ref` adapter contracts. Prefer properties over hand-picked single examples wherever an invariant holds over a domain; reserve example tests for regression pins and imperative I/O wiring.
- **Standard profiles ([tests/conftest.py](tests/conftest.py)):** Select via `HYPOTHESIS_PROFILE=dev|ci|thorough` (all `deadline=None`):
  - `dev` — `50` examples (default local).
  - `ci` — `100` examples, deterministic (`derandomize=True`).
  - `thorough` — `1000` examples (pre-release / stress).
- **Required property categories for new modules:**
  1. **Algebraic / monad laws:** Functor identity and composition, monad left/right identity and associativity, `Either` tag/match symmetry, and error-channel mapping.
  2. **Parse / serialize round-trip laws:** Deterministic JSON and wire round-trips (`NullableOption` without falsy/`NOTHING` confusion, `Either`, `PersistentMap`, `PersistentSet`, `JsonValue`, `SKILL.md` frontmatter).
  3. **Immutability & strict-rejection laws:** `_evolve()` never mutates the original instance; `strict=True` rejects silent coercions (`bool`-as-`int`, etc.); `extra="forbid"` rejects unknown keys.
  4. **Security, confinement & redaction invariants:** Non-leakage and idempotence of `SecretVault` / `RedactedStr`, capability-token enforcement, traversal/confinement rejection (`RelativeRepoPath`, `ConfinedScratchPath`), and holdout split isolation.

## Shell Conventions

- Declare the target dialect explicitly (`Bash 4.4+` or POSIX `sh`). Follow Google Shell Style (`lower_snake_case` locals/functions, `namespace::lower_snake_case` library functions, `readonly` `UPPER_SNAKE_CASE` constants, quoted expansions, separate `local` declaration from command substitution).
- Never silence failing helpers or hide stderr/exit codes. Gate every touched shell script with `bash -n` and [.agents/skills/shell-gate/scripts/shell-gate.sh](.agents/skills/shell-gate/scripts/shell-gate.sh).

## Installed Repo Python & Shell Skills

All `30` `artagon-python` skills and `8` `artagon-shell` skills are installed under `.agents/skills/` and exposed to Claude Code via `.claude/skills -> ../.agents/skills`. Read the matching `SKILL.md` before executing the corresponding task; apply every cited skill and never cite a skill without following it.

### Core Python Workflow Routing

| Task | Required Installed Skills |
| --- | --- |
| Domain models, types, protocols, ADTs | [python-type-safety](.agents/skills/python-type-safety/SKILL.md), [python-design-patterns](.agents/skills/python-design-patterns/SKILL.md) |
| Authoring & formatting Python code | [python-code-style](.agents/skills/python-code-style/SKILL.md), [python-anti-patterns](.agents/skills/python-anti-patterns/SKILL.md), [py-modernize](.agents/skills/py-modernize/SKILL.md) |
| Error handling, structured logs, telemetry | [python-error-handling](.agents/skills/python-error-handling/SKILL.md), [python-observability](.agents/skills/python-observability/SKILL.md), [python-resilience](.agents/skills/python-resilience/SKILL.md), [python-resource-management](.agents/skills/python-resource-management/SKILL.md) |
| Workspace layout, packaging, `uv`, config | [python-project-structure](.agents/skills/python-project-structure/SKILL.md), [python-packaging](.agents/skills/python-packaging/SKILL.md), [uv-package-manager](.agents/skills/uv-package-manager/SKILL.md), [python-configuration](.agents/skills/python-configuration/SKILL.md) |
| Unit, fixture, and property tests | [python-testing-patterns](.agents/skills/python-testing-patterns/SKILL.md), [pytest-code-review](.agents/skills/pytest-code-review/SKILL.md), [py-test-quality](.agents/skills/py-test-quality/SKILL.md) |
| Complexity, dead code, refactoring | [py-complexity](.agents/skills/py-complexity/SKILL.md), [py-code-health](.agents/skills/py-code-health/SKILL.md), [py-refactor](.agents/skills/py-refactor/SKILL.md), [python-performance-optimization](.agents/skills/python-performance-optimization/SKILL.md) |
| Security, static gates, pre-commit hooks | [py-security](.agents/skills/py-security/SKILL.md), [py-quality-setup](.agents/skills/py-quality-setup/SKILL.md), [py-git-hooks](.agents/skills/py-git-hooks/SKILL.md) |
| Code review & verification | [python-code-review](.agents/skills/python-code-review/SKILL.md), [review-python](.agents/skills/review-python/SKILL.md), [review-verification-protocol](.agents/skills/python-code-review/references/companion-skills/review-verification-protocol/guide.md) |
| Async / jobs & specialized backend reviews | [async-python-patterns](.agents/skills/async-python-patterns/SKILL.md), [python-background-jobs](.agents/skills/python-background-jobs/SKILL.md), [fastapi-code-review](.agents/skills/fastapi-code-review/SKILL.md), [sqlalchemy-code-review](.agents/skills/sqlalchemy-code-review/SKILL.md), [postgres-code-review](.agents/skills/postgres-code-review/SKILL.md) |

### Shell Workflow Routing

| Task | Required Installed Skills |
| --- | --- |
| Authoring, refactoring, or hardening shell scripts | [shell-authoring](.agents/skills/shell-authoring/SKILL.md), [shell-defensive](.agents/skills/shell-defensive/SKILL.md) |
| Dialect contracts (Bash / POSIX / Zsh) | [shell-bash](.agents/skills/shell-bash/SKILL.md), [shell-posix](.agents/skills/shell-posix/SKILL.md), [shell-zsh](.agents/skills/shell-zsh/SKILL.md) |
| Static analysis, Bats/ShellSpec tests, quality gate | [shell-linting](.agents/skills/shell-linting/SKILL.md), [shell-testing](.agents/skills/shell-testing/SKILL.md), [shell-gate](.agents/skills/shell-gate/SKILL.md) |

## OpenSpec Change Management

- This repository uses OpenSpec `2.1.0` with the local [`spec-driven-evidence`](openspec/schemas/spec-driven-evidence/schema.yaml) schema configured in [openspec/config.yaml](openspec/config.yaml).
- Discover active changes and artifact readiness with `openspec list` and `openspec status --change <change-id>`. Read [openspec/project.md](openspec/project.md), [openspec/AGENTS.md](openspec/AGENTS.md), and the target change's `proposal.md`, `specs/`, `design.md`, and `tasks.md` before editing spec text.
- Keep capability specs normative (`SHALL`/`MUST`), concise (`< 450` chars per requirement body), and scenario-backed (`GIVEN`/`WHEN`/`THEN`); never check off tasks or claim verification without observed proof in the same worktree.
- Run `openspec validate --all --strict` before handoff or commit.

## Verification Commands

Run the full quality gate before handing off or committing changes:

```bash
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

Run deterministic CI or thorough pre-release/stress property verification via `HYPOTHESIS_PROFILE`:

```bash
HYPOTHESIS_PROFILE=ci uv run --frozen pytest -m property --fail-on-skip -q
HYPOTHESIS_PROFILE=thorough uv run --frozen pytest -m property --fail-on-skip -q
```

For shell scripts and Nix verification:

```bash
bash -n <script.sh>
.agents/skills/shell-gate/scripts/shell-gate.sh <script.sh>
nix-instantiate --parse flake.nix
uv run --frozen harness-eval --help && uv run --frozen skill-eval --help && uv run --frozen skill-lint --help
```
