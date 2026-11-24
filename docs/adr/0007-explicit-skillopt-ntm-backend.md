---
status: accepted
date: 2026-11-06
decision-makers: []
consulted: []
informed: []
---

# ADR-0007: Integrate SkillOpt through an explicit NTM-backed Sleep Backend

## Status

Accepted.

## Context

SkillOpt 0.2.0 has unknown-name mock fallback, no sleep-cycle backend injection,
and unsafe empty-split fallback for this experiment contract. The integration
must preserve native call ownership, development-only feedback and bundle lineage.

## Decision

Use pinned, integrity-checked SkillOpt 0.2.0 through an explicitly constructed
custom Sleep Backend passed to `consolidate(backend, ...)`. Route target,
reflection and selection through the existing experiment-owned NTM interface.
Reject incompatible APIs and empty/overlapping development splits before calls
or writes. Never use name factories, whole sleep-cycle orchestration, inherited
response caches or estimated tokens as native measurements. Reserve budget even
for real-backend dry-runs. Materialize bounded complete candidates with base
hashes, path allowlists, factors and lineage inside the candidate area. Keep final
holdouts out of optimization; `@adr:0005` governs promotion patches.

## Alternatives considered

- Chosen: explicit custom backend and consolidation, with a version-specific adapter.
- Rejected: name factories/sleep cycle, due to fallback and missing injection.
- Rejected: separate direct-provider runner, which splits lifecycle/budget ownership.

## Consequences

Optimizer and eval calls share receipts and budget controls. Upstream API changes
block until reviewed. Bundle materialization adds checks; production remains intact.

## Links to OpenSpec change

- `@change:add-scientific-skill-experiments`
- `openspec/changes/add-scientific-skill-experiments/proposal.md`
- `openspec/changes/add-scientific-skill-experiments/design.md`
- `openspec/changes/add-scientific-skill-experiments/tasks.md`

## Links to affected requirements

- `@spec:skill-structure-optimization#skillopt-uses-a-pinned-reviewed-interface`
- `@spec:native-skill-evaluation#native-trials-have-one-lifecycle-owner`

## Links to tests and evidence

Tasks 5.1–5.3 and 6.4 owe API/fallback/cache, bundle-edit and actual native
optimization checks. Inert integration checks are recorded in
`openspec/changes/add-scientific-skill-experiments/evidence/optimization.md`;
actual native optimization remains pending.

## Related decisions

`@adr:0005` governs evidence admission and promotion eligibility.

## Supersedes / superseded by

- Supersedes: N/A
- Superseded by: N/A
