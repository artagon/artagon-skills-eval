---
status: accepted
date: 2026-11-14
decision-makers: []
consulted: []
informed: []
---

# ADR-0010: Isolate harness-eval Nix closure, per-trial tmux servers, and ephemeral CAO daemons

## Status

Accepted.

## Context

`nix/skill-experiments/` intentionally keeps a minimal stdlib-focused closure,
whereas `harness-eval` requires `duckdb`, `pyarrow`, `opentelemetry-proto`,
`jsonschema`, `pyyaml`, and `hypothesis`. Furthermore, Tier-2 multiplexers (`NTM`,
`Herdr`, `CAO`) default to shared `tmux` sockets, login shells sourcing `~/.zshrc`
or `~/.bashrc`, and the singleton `cao-server` on `127.0.0.1:9889`, which can
re-inject API keys or collide with active operator sessions.

## Decision

1. Ship a dedicated staged locked flake under `nix/harness-eval/{flake.nix.in,flake.lock.in}`
   sharing the pinned `nixpkgs` revision from `nix/skill-experiments/flake.lock.in`
   and staged via an explicit public allowlist (`@adr:0006` pattern).
2. Pre-start a private `tmux` server (`TMUX_TMPDIR=<trial>/tmux`, `-L art-eval`)
   with `-f <trial>/tmux.conf` setting `default-command` to
   `bash --noprofile --norc` (`rc-free-bash`) before any `NTM` or `CAO` call.
3. Launch an ephemeral bearer-authenticated `cao-server` on `127.0.0.1:0` backed
   by `<trial>/cao/cao.db` and `<trial>/cao/profiles/`, leaving any operator
   `cao-server` on `127.0.0.1:9889` untouched.
4. For `Herdr`, bind `HOME=<trial>/pane-home` (`unsetopt GLOBAL_RCS`) and pass
   `--no-brief`.

## Alternatives considered

- Chosen: separate `nix/harness-eval/` staged closure + private `tmux -f` +
  ephemeral `cao-server`.
- Rejected: bloating `nix/skill-experiments/` with Arrow/DuckDB native wheels.
- Rejected: reusing the live `127.0.0.1:9889` `cao-server` or default `tmux`
  socket, which contaminates shell RC environments and operator sessions.

## Consequences

Tier-2 evaluations run deterministically alongside live operator swarms without
port, profile, or dotfile collisions, at the cost of a lightweight per-trial
`tmux` and `cao-server` process lifecycle.

## Links to OpenSpec change

- `@change:add-subscription-harness-eval`
- `openspec/changes/add-subscription-harness-eval/proposal.md`
- `openspec/changes/add-subscription-harness-eval/design.md`
- `openspec/changes/add-subscription-harness-eval/tasks.md`

## Links to affected requirements

- `@spec:subscription-harness-evaluation#isolated-trial-homes-mcp-cassettes-and-tier-1tier-2-parity`

## Links to tests and evidence

Verified by `tests/test_harness_eval_environment.py`,
`scripts/harness-eval-nix-check.py`, `tests/herdr-swarm.bats`, and
`tests/test_harness_eval_tier2_backends.py`.

## Supersedes / superseded by

- Supersedes: N/A
- Superseded by: N/A
