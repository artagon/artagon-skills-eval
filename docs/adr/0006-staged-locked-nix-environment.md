---
status: accepted
date: 2026-11-06
decision-makers: []
consulted: []
informed: []
---

# ADR-0006: Run locked Nix tooling from host-staged public sources

## Status

Accepted.

## Context

A locked environment distinguishes local dependency drift from skill effects.
Filtering after Nix captures a repository root can already expose excluded files
to the store. Reproducible local tools do not reproduce hosted model behavior.

## Decision

Keep flake and lock `.in` templates in the checkout. Create the live flake and
lock only in a fresh external public stage populated by a host-side explicit
public allowlist before repository-root capture, then invoke locked Nix tooling
through `path:<stage>`. Manifest the flake, lock and required sources with
validated identities. Exclude homes, credentials,
logs, results, candidates and protected cases; reject unsafe or changed identities.
Locked execution neither rewrites locks nor substitutes dependencies. Cached
deterministic checks run offline; absent inputs fail explicitly. Unpackaged
vendor clients remain observed external dependencies.

## Alternatives considered

- Chosen: host-side staging before capture, with explicit manifests and identity checks.
- Rejected: root capture followed by filters, which ingests excluded material first.
- Rejected: mutable host dependencies, which retain drift.

## Consequences

Bounded provenance requires staging/platform maintenance. Uncached offline inputs
cannot be fetched silently. Authentication and external clients remain separate.

## Links to OpenSpec change

- `@change:add-scientific-skill-experiments`
- `openspec/changes/add-scientific-skill-experiments/proposal.md`
- `openspec/changes/add-scientific-skill-experiments/design.md`
- `openspec/changes/add-scientific-skill-experiments/tasks.md`

## Links to affected requirements

- `@spec:reproducible-ai-tooling#locked-dependencies-define-the-local-environment`

## Links to tests and evidence

Task 4.1 is recorded complete. Scoped host staging and locked/offline checks are
recorded in
`openspec/changes/add-scientific-skill-experiments/evidence/environment.md`;
tasks 4.2–4.3 and final review remain open, and other platforms are unverified.

## Supersedes / superseded by

- Supersedes: N/A
- Superseded by: N/A
