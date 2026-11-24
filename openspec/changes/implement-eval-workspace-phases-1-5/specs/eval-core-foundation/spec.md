# Capability: eval-core-foundation

## ADDED Requirements

### Requirement: Pure Frozen Domain Models and Typestates
All records under `artagon_eval_core.domain` SHALL inherit `FrozenModel` (`frozen=True`, `extra="forbid"`, `strict=True`) with immutable containers only (`tuple`, `frozenset`, `PersistentMap`, `PersistentSet`) and zero `Any` or I/O imports. Lifecycle and auth invariants SHALL be encoded via `DraftProtocol -> ResolvedProtocol -> FrozenManifest` and `SubscriptionAuth | ApiKeyAuth`.

#### Scenario: Rejecting API-key arm on subscription-only surface
- GIVEN a `DraftProtocol` containing an `ApiKeyAuth` arm
- WHEN `for_skill_eval_surface()` is evaluated
- THEN it SHALL return `Error(BillingGuardError)` with exit code `4` and leave the original draft unchanged.

#### Scenario: Rejecting arm mutation on a frozen manifest
- GIVEN a `FrozenManifest` produced from a validated `ResolvedProtocol`
- WHEN a caller attempts to invoke `.with_arm_override(...)` or mutate any nested field
- THEN static type checking (`basedpyright --strict`, `mypy --strict`) and runtime validation SHALL reject the operation.

### Requirement: Single Canonical Billing, Split, and Redaction Boundaries
The core package SHALL provide one canonical `METERED_BILLING_ENV_VARS` policy, one `parse_task_split` normalizer (`train|development`, `val|selection`, `test|holdout`), and capability-sealed `RedactedStr` minted exclusively by `SecretVault` / `SecretScrubberPort` or compile-time literal `static_redacted_literal(...)`.

#### Scenario: Rejecting raw string construction of RedactedStr
- GIVEN an unredacted runtime string containing an API token
- WHEN code passes it directly to `RedactedStr(...)` or an `EvalError.message` field
- THEN direct construction SHALL raise `TypeError`, Pydantic validation SHALL fail, and static type checkers SHALL report an error.

#### Scenario: Normalizing split aliases deterministically
- GIVEN arbitrary casing and surrounding whitespace around `development`, `selection`, or `holdout`
- WHEN `parse_task_split` evaluates the input
- THEN it SHALL return `Ok("train")`, `Ok("val")`, or `Ok("test")`, and any unknown token SHALL return `Error(SplitDataError)` (`exit 65`).

### Requirement: Typed Effect Ports and Shared Runtime Primitives
Side-effectful capabilities SHALL be declared as `Protocol` interfaces under `artagon_eval_core.ports` returning `EvalResult[T]`. Shared execution controls (`CampaignAbortLatch`, `LaunchBudget`, `ChildEnvBuilder`, `ProposerPort`, `jcs`, `pins`, `patch`, `curation`) SHALL reside once in `artagon_eval_core.runtime` so adapters never duplicate them.

#### Scenario: Structured logging scrubs registered secrets on stderr
- GIVEN a `SecretVault` with a registered high-entropy secret and a `structlog` stderr logger
- WHEN `log_eval_error` logs an `EvalError` containing text processed through `SecretVault.scrub()`
- THEN the emitted `stderr` record SHALL carry `reason_code`, `exit_code`, and zero occurrences of the raw secret.

### Requirement: Lazy Pluggy Adapter Registry and Fail-Closed Discovery
`artagon_eval_core.plugins` SHALL define Pluggy hookspecs and discover adapters lazily via `importlib.metadata.entry_points()` without importing adapter modules at CLI startup. Requesting an uninstalled adapter SHALL return `Error(AdapterUnavailableError)` mapping to exit code `69` with install guidance.

#### Scenario: Missing optional adapter fails closed with exit 69
- GIVEN an environment where `artagon-eval-waza` is not installed
- WHEN a command resolves the `waza` benchmark adapter via `PluginRegistry`
- THEN it SHALL return `Error(AdapterUnavailableError)` with `exit_code = 69`, `adapter_name = "waza"`, and `install_extra = "waza"`.

### Requirement: ADR-0006 Offline Nix Packaging, Version Bounds, and SPDX Guard
`flake.nix` and `artagon_eval_core.packaging` SHALL enforce ADR-0006 clean-source `lib.fileset` slicing, eval-time forbidden-file rejection, `O_NOFOLLOW` `0700` host staging, `nix/locked-versions.json` parity for both `packages` and `tools`, zero-dependency AST boundary checking, and a 4-step SPDX license guard with zero Step-4 core/dev overrides and zero `Elastic-2.0` pulls.

#### Scenario: Dirty checkout with forbidden root file fails closed at Nix eval
- GIVEN a source tree containing `.env`, `.venv`, `scratch`, or `holdouts`
- WHEN Nix evaluates `flake.nix` directly on that tree or `stage_environment()` scans the directory
- THEN evaluation or staging SHALL abort with an explicit ADR-0006 error without copying forbidden files to `/nix/store/`.
