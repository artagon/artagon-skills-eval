---
status: proposed
date: 2026-11-15
decision-makers: []
consulted: []
informed: []
---

# ADR-0012: Package `artagon-harness-eval` as a standalone capability-driven Python project with deeply frozen Pydantic models and Pluggy hooks

## Status

Proposed.

## Context

`artagon-harness-eval` (`@adr:0009`, `@adr:0010`, `@adr:0011`) currently scatters its
Python modules across `artagon-scripts/scripts/lib/harness_eval_*.py`, mirrors `35`
files into `plugins/artagon-harness-eval/scripts/` via `configs/plugin-runtime-map.json`,
runs `9` dedicated `tests/test_harness_eval_*.py` suites (plus `3` companion suites)
from root `tests/`, couples to `artagon-scripts` helpers (`keychain.sh`,
`herdr_swarm.sh`, `art_swarm`, `skill_experiment_native.py`), and encodes vendor CLI
differences through `114` hardcoded CLI-name branches, `32` mutable dataclasses, `707`
`dict[str, Any]` annotations, and Grade-`F` functions (`CC=96..186`). Maintainers plan
to extract `artagon-harness-eval` into its own repository
(`github.com/artagon/artagon-harness-eval`) and need CLI drift updates to require
declarative YAML edits rather than Python subclassing.

## Decision

1. **Canonical Standalone Python Project in `plugins/artagon-harness-eval/`**:
   Establish `plugins/artagon-harness-eval/` as a complete PEP 621 project
   (`[project] name = "artagon-harness-eval"`, `requires-python = ">=3.12"`,
   `hatchling` build backend, dependency lower bounds `<=` plugin-committed
   `nix/harness-eval/locked-versions.json`, `src/artagon_harness_eval/` layout with
   `py.typed` and `data/` subpackages loaded via `importlib.resources`, `uv.lock`,
   dedicated CI `.github/ci/requirements-harness-eval.txt`, Python-`3.9`-parseable
   stdlib-only bootstrap launchers in `scripts/`, and uniquely named `tests/test_ahe_*.py`
   modules ported `1:1` from the `9` root `tests/test_harness_eval_*.py` suites)
   verified to pass `uv run --frozen pytest` and offline Nix checks inside a
   `git subtree split` worktree. Retire the `35`-entry `plugin-runtime-map.json` copy
   map via ordered orphan cleanup (`plugins/artagon-harness-eval/scripts/**`), retire
   the `9` duplicate `tests/test_harness_eval_*.py` files in `B8` (verified via
   `tests/fixtures/root_test_migration_map.json`), hash full `src/` + `data/` in
   `apm-plugin-adapters.json` `host_runtime_refs`, and retain thin root facades for
   `keychain_store.py`, `mcp_cassette.py`, `judge_sanitize.py`, and
   `skill_experiment_skillopt.py` until repo split.
2. **Two-Tier Deeply Frozen Functional Architecture**:
   - Control plane (`models.py`, `catalog.py`, `planner.py`, `otlp_sink.py`,
     `outcome.py`) uses Pydantic v2 `ConfigDict(frozen=True, extra="forbid")` plus
     recursive `FrozenMap` (`types.MappingProxyType`)/`tuple` deep-freezing (structural
     equality without claiming `hash()` on `FrozenMap` fields), `pyyaml` safe loading,
     exact `0cc2b0a` `SystemPromptCapability` routes (`default`/`append`/`replace`),
     `packaging` SemVer `SpecifierSet` overlays, `returns.result` pure trial planning,
     pre-freeze `/nix/store/` binary enforcement (`--allow-host-pin` downgrade),
     `rfc8785` canonical JSON with exact `uint64` fallback above `2**53 - 1`, `tomlkit`
     (`>=0.14.0`), sandboxed `jinja2`, in-process loopback `otlp_sink.py` (`protobuf`
     `7.34.1` + `opentelemetry-proto` `1.34.0`), `jmespath` + pure OTel stream-epoch
     reducers, `detect-secrets` `SecretVault`, strictly read-only method-only Linux
     `xdg-dbus-proxy` (`keyring.py` omitting BOTH `--talk=org.freedesktop.secrets` and
     state-mutating `Unlock`), exact `trace.schema.json` wire outcome statuses (`v1`
     scoped to `claude`, `codex`, `agy`, `copilot`), and `typer` (`exit 0,2..8`).
   - Hot-path subprocess shims (`shims/{wire,scrub,trampoline,hook_sink}.py`) execute
     under `<shim_python_executable> -P -s -m artagon_harness_eval.shims.<name>`
     (`>=3.12`, `PYTHONSAFEPATH=1`, immune to workspace `cwd` `sys.path[0]` shadowing),
     decode `HotPathShimDescriptor` via `shims/wire.py` (`msgspec.Struct(frozen=True)`
     or `@dataclass(frozen=True)` without `slots=True`), enforce a namespace +
     `__file__` origin `sys.modules` predicate (zero `pydantic`, `detect_secrets`,
     `yaml`, `typer`, `pluggy`, `duckdb`, `pyarrow`, `google`, `opentelemetry` imports),
     and satisfy an accepted replacement two-part fresh-subprocess latency contract
     (`median(T_cold_shim) - median(T_cold_empty_python_c_pass) <= 5ms` across `21`
     fresh `-P -s` invocations + `p95 <= 250ms` Unix-socket round-trip + `4s` `SIGALRM`
     fail-open watchdog, replacing raw `<5ms` subprocess startup which is physically
     impossible on Darwin where bare `python3 -P -s -c pass` takes `~30–160ms`).
3. **Reusable `pluggy` Hook Compiler & Separated Target Routing**:
   Use `pluggy.PluginManager("harness_core")` to decouple hook producers from
   `HookTargetRouting` (Claude `$CLAUDE_CONFIG_DIR/settings.json` + `.claude/settings.json`,
   Codex `$CODEX_HOME/hooks.json` + `.codex/hooks.json`, Agy `$HOME/.gemini/config/hooks.json`
   + `.agents/hooks.json`, Copilot `$COPILOT_HOME/hooks/eval-trace.json` +
   `.github/hooks/harness-eval.json`)
   and the four vendor wire codecs (`nested_matcher_groups`, `namespaced_lifecycle`,
   `versioned_flat_map`, `event_array`).

## Alternatives considered

- **Chosen**: Self-contained `plugins/artagon-harness-eval/` PEP 621 package +
  deeply frozen `pydantic` (`MappingProxyType`) / `-P -s -m` `msgspec`+stdlib shims +
  declarative YAML capability catalog + `pluggy` hooks.
- **Rejected**: Keeping canonical code in `artagon-scripts/scripts/lib/` with
  `plugin-runtime-map.json` mirroring, which blocks clean `git subtree split`
  extraction and broke standalone Nix `checks.offline` (`discussion_r4580748717`).
- **Rejected**: Bare `python -m` without `-P -s`, which prepends trial workspace `cwd`
  (`""`) to `sys.path[0]` ahead of stdlib (`OPUS-201`).
- **Rejected**: Passing `--talk=org.freedesktop.secrets` or `Service.Unlock` to
  `xdg-dbus-proxy`, which permits write calls (`ASTRA-01`) or mutates host keyring
  collection lock state (`ASTRA-201`).
- **Rejected**: Shallow `Mapping[K, V]` without `MappingProxyType` (`ASTRA-02`,
  `SOL-04`) or unwrapped `rfc8785.dumps` without `uint64` fallback (`SOL-01`).

## Consequences

`plugins/artagon-harness-eval/` tests, builds via `uv` and offline Nix, emits clean
JSON envelopes on Python `<3.12` or stdlib-only `>=3.12` hosts, and splits into its
own repository in one `git subtree split` command without rewriting imports.

## Links to OpenSpec change

- `@change:extract-capability-driven-artagon-harness-eval`
- `openspec/changes/extract-capability-driven-artagon-harness-eval/proposal.md`
- `openspec/changes/extract-capability-driven-artagon-harness-eval/design.md`
- `openspec/changes/extract-capability-driven-artagon-harness-eval/tasks.md`

## Links to affected requirements

- `@spec:standalone-harness-eval-package#standalone-pep-621-artagon-harness-eval-package-version-bounds-and-isolated-test-suite`
- `@spec:standalone-harness-eval-package#stdlib-only-bootstrap-launchers-ordered-copy-map-retirement-and-symbol-compatible-shims`
- `@spec:capability-harness-core#deeply-frozen-control-plane-models-and-strict-shim-isolation`
- `@spec:capability-harness-core#declarative-6-cli-capability-catalog-system-prompt-modes-semver-overlays-and-uint64-jcs`
- `@spec:capability-harness-core#method-only-read-only-linux-d-bus-proxy-nixstore-freeze-gate-and-traceschemajson-outcomes`
- `@spec:pluggy-hook-framework#pluggy-hook-compilation-separated-target-routing-and-non-destructive-4-dialect-merging`
- `@spec:skillopt-multi-cli-bridge#multi-cli-subscription-skillopt-bridge-and-transcript-harvesting`

## Links to tests and evidence

Verified by `plugins/artagon-harness-eval/tests/packaging/test_ahe_repo_independence.py`,
`plugins/artagon-harness-eval/tests/test_ahe_catalog_properties.py`,
`plugins/artagon-harness-eval/tests/test_ahe_hooks.py`, and
`plugins/artagon-harness-eval/tests/test_ahe_planner_properties.py`.

## Supersedes / superseded by

- Supersedes: N/A (extends `@adr:0009`, `@adr:0010`, `@adr:0011`)
- Superseded by: N/A
