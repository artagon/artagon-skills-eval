# About `artagon-skills-eval`

`artagon-skills-eval` is a standalone, subscription-first Python and Nix evaluation platform for Agent Skills and multi-CLI coding harnesses (`claude`, `codex`, `agy`, `copilot`, `kimi`).

## Design Guarantees

1. **Functional Core / Imperative Shell (FCIS):** Pure domain models under `artagon_eval_core.domain` carry zero I/O, subprocess, CLI, or database imports. Side effects enter strictly through typed `Protocol` ports in `artagon_eval_core.ports`.
2. **Make Illegal States Unrepresentable:**
   - Every domain record inherits strict, deeply frozen `FrozenModel` (`frozen=True`, `extra="forbid"`, `strict=True`, `validate_default=True`) using `tuple`, `frozenset`, and `rpds-py` persistent containers (`PersistentMap`, `PersistentSet`).
   - Algebraic `Option[T]`, `Result[T, E]`, and symmetric `Either[L, R]` (`@case` `TaggedUnion`) come directly from `Expression` (`expression[pydantic]`), with `NullableOption[T]` preserving Draft 2020-12 JSON wire compatibility.
   - `DraftProtocol -> ResolvedProtocol -> FrozenManifest`, `SubscriptionAuth | ApiKeyAuth`, `TrainEvalCase | ValEvalCase | TestEvalCase`, and `GateAccepted -> PromotionPatch` enforce critical invariants at compile time (`basedpyright --strict` + `mypy --strict`) and parse boundaries.
3. **Compile-Time & Runtime Secret Redaction:** `RedactedStr` is a sealed `str` subclass that cannot be instantiated directly from raw `str`; only `SecretVault` / `SecretScrubberPort` (or compile-time constant `static_redacted_literal(...)`, enforced by `ast-grep`) can mint it. Every CLI failure logs redacted diagnostics to `stderr` via `structlog`, making silent failures impossible.
4. **Decoupled Lazy Adapters:** External integrations (`waza`, `dspy`, `skillopt`, `evoskill`, `skillspec`, `observability`) live in independent workspace packages registered through Pluggy and `importlib.metadata` entry points. Missing adapters fail closed with `AdapterUnavailableError` (`exit 69`).
5. **Official Spec Reuse:** `agentskills.io`'s official `skills-ref` handles Tier-0 `SKILL.md` parsing and specification validation strictly inside `artagon_eval_skills.spec_adapter`.
6. **ADR-0006 Hermetic Nix Packaging:** `flake.nix` enforces `lib.fileset.toSource` clean-source filtering and an evaluation-time forbidden-file assertion so secrets, `.env`, `.venv`, holdouts, or scratch outputs never enter `/nix/store/`.
7. **ADR-0012 Hot-Path Shim Isolation:** `artagon_eval_core.shims` imports only the Python standard library and optional `msgspec`, enforced mechanically by `import-linter`.

## Mechanical Verification Gates

| Gate | Tool | Contract |
| --- | --- | --- |
| Unit & Property Tests | `pytest` + `hypothesis` | Workspace tests (`packages/*/tests`, `tests/`) with `--import-mode=importlib` |
| Static Typing (Dual Checker) | `basedpyright --strict` + `mypy --strict` | `reportAny="error"`, `reportExplicitAny="error"`, `reportUnusedCallResult="error"`, `exhaustive-match` |
| Linting & Complexity | `ruff check` + `radon cc -n C` | McCabe `max-complexity = 8`, zero `C` or worse functions in `packages/*/src` |
| Architecture Boundaries | `lint-imports` (`import-linter`) | 6 contracts: FCIS layers, pure domain, hot-path shims, core/adapter isolation, adapter independence, `skills-ref` isolation |
| Structural Lint | `ast-grep` (`sgconfig.yml`) | 5 Python rules + snapshot tests in `rules/python/` and `rule-tests/` |
| Hermetic Nix | `flake.nix` + `nix/locked-versions.json` | `nixos-26.05` pinned closure, ADR-0006 forbidden-file assert, offline check |
