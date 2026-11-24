# wshobson-shell-scripting — Upstream Source

- **Upstream repo**: https://github.com/wshobson/agents
- **Upstream license**: MIT (see `LICENSE.upstream`)
- **Vendored commit SHA**: `c15b108a8d2fa853140b811e2dffdc30bd0ce788`
- **Vendored at**: 2026-05-01

Plugin imported as part of the absorb-beagle-wshobson-mcollina change Phase 3.

**Phase 4 — COMPLETED 2026-05-17** under
`openspec/changes/consolidate-artagon-shell-skills/`. Renamed the three
vendored skills (`bash-defensive-patterns` → `shell-defensive`,
`shellcheck-configuration` → `shell-linting`, `bats-testing-patterns`
absorbed into `shell-testing/references/bats-patterns.md`), tightened
each SKILL.md body under the ≤145-line progressive-disclosure cap, and
added a new `shell-gate` skill shipping a runnable
`scripts/shell-gate.sh` plus per-CLI hook recipes (Claude PostToolUse,
Codex PreToolUse, Gemini BeforeTool). The plugin now ships 5 curated
skills: `shell-authoring`, `shell-defensive`, `shell-linting`,
`shell-testing`, `shell-gate`. MIT-licensed source content from
`wshobson/agents@c15b108` is preserved verbatim in the destination
`references/` files; attribution footers retained per upstream license.
