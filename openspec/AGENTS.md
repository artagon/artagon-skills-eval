# OpenSpec Instructions (`artagon-skills-eval`)

## Scope

This directory holds OpenSpec `2.1.0` configuration ([`config.yaml`](config.yaml)), project context ([`project.md`](project.md)), the `spec-driven-evidence` workflow schema ([`schemas/spec-driven-evidence/schema.yaml`](schemas/spec-driven-evidence/schema.yaml)), promoted capability specs (`specs/`), and active changes (`changes/`).

Before editing any specification or change artifact, read:
1. [`../AGENTS.md`](../AGENTS.md) for repository-wide typing, security, and testing contracts.
2. [`project.md`](project.md) for change sequencing and tech stack boundaries.
3. The target change's `proposal.md`, `specs/`, `design.md`, and `tasks.md`.

## Discovering Active Changes

Run these commands from the repository root instead of assuming a single hardcoded change:

```bash
openspec list
openspec status --change <change-id>
```

## Editing Rules

- **Normative specs:** Write requirements with `SHALL` or `MUST`. Keep each requirement body under 450 characters so `openspec validate --strict` passes with zero warnings.
- **Scenarios required:** Every `### Requirement:` MUST include at least one `#### Scenario:` block with `- GIVEN`, `- WHEN`, and `- THEN`.
- **Delta discipline:** Use `## ADDED Requirements` for capabilities not yet in `openspec/specs/`. Check both `openspec/specs/` and sibling `openspec/changes/*/specs/` before naming a new capability.
- **Honest tracking:** Never mark a task `[x]` in `tasks.md` unless both implementation and verification passed in the same worktree. Keep unexecuted items in `evidence/README.md`, `review.md`, and `verification.md` explicitly marked `not checked`, `pending`, or `not run`.
- **Architecture alignment:** Cross-check cited package paths, CLI commands, `import-linter` contracts, and Nix targets against live files ([`../pyproject.toml`](../pyproject.toml), [`../flake.nix`](../flake.nix), `packages/`).
- **Public repository hygiene:** Use repository-relative paths only. Never write local home paths, corporate domains, personal emails, local file-scheme URIs, or secret values into any OpenSpec artifact.

## Validation

Run strict validation after every OpenSpec edit and before commit:

```bash
openspec list
openspec status --change <change-id>
openspec validate --all --strict
```
