# Repository Provenance

`artagon-skills-eval` was bootstrapped as a clean greenfield repository extracted from committed assets in `artagon/artagon-scripts`.

## Origin Snapshot

| Field | Value |
| --- | --- |
| Origin Repository | `github.com/artagon/artagon-scripts` |
| Origin Commit SHA | `4bc7df28c98704b344c91fce2c710d182a72144b` |
| Origin Commit Timestamp | `2026-11-23 12:38:14 -0500` |
| Origin Commit Subject | `Merge pull request #35 from artagon/feat/add-minijinja-skills` |
| Extraction Method | Clean `git archive <ORIGIN_SHA>` (zero dirty working-tree contamination) |
| Bootstrap Strategy | Clean greenfield `git init -b main` with explicit provenance (`Origin-Repo` trailer) |

## Extracted Committed Asset Lineage

| Destination in `artagon-skills-eval` | Origin Path in `artagon-scripts@4bc7df28` |
| --- | --- |
| `docs/adr/0005-scientific-evidence-admission.md` | `docs/adr/0005-scientific-evidence-admission.md` |
| `docs/adr/0006-staged-locked-nix-environment.md` | `docs/adr/0006-staged-locked-nix-environment.md` |
| `docs/adr/0007-explicit-skillopt-ntm-backend.md` | `docs/adr/0007-explicit-skillopt-ntm-backend.md` |
| `docs/adr/0009-harness-eval-dual-auth-and-keychain-separation.md` | `docs/adr/0009-harness-eval-dual-auth-and-keychain-separation.md` |
| `docs/adr/0010-harness-eval-ephemeral-cao-and-tmux-isolation.md` | `docs/adr/0010-harness-eval-ephemeral-cao-and-tmux-isolation.md` |
| `docs/adr/0011-harness-eval-four-layer-trace-and-duckdb-store.md` | `docs/adr/0011-harness-eval-four-layer-trace-and-duckdb-store.md` |
| `docs/adr/0012-standalone-capability-driven-artagon-harness-eval.md` | `docs/adr/0012-standalone-capability-driven-artagon-harness-eval.md` |
| `docs/adr/0015-waza-and-dspy-gepa-harness-eval-bridges.md` | `docs/adr/0015-waza-and-dspy-gepa-harness-eval-bridges.md` |
| `docs/adr/0016-unified-subscription-skill-eval-and-adapter-architecture.md` | `docs/adr/0016-unified-subscription-skill-eval-and-adapter-architecture.md` |
| `skills/{harness-eval,harness-eval-author,harness-eval-trace}/` | `plugins/artagon-harness-eval/skills/` |
| `examples/` | `plugins/artagon-harness-eval/examples/` |
| `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/` (9 schemas) | `plugins/artagon-harness-eval/src/artagon_harness_eval/data/schemas/` |
| `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/skill-eval-result.schema.json` | `configs/skill_eval_result.schema.json` |
| `packages/artagon-eval-core/src/artagon_eval_core/data/harnesses/` (6 YAMLs) | `plugins/artagon-harness-eval/src/artagon_harness_eval/data/harnesses/` |
| `packages/artagon-eval-core/src/artagon_eval_core/data/providers.json` | `plugins/artagon-harness-eval/configs/art-swarm/providers.json` |
| `packages/artagon-eval-core/src/artagon_eval_core/data/keychain-services.json` | `plugins/artagon-harness-eval/src/artagon_harness_eval/data/keychain-services.json` |
| `flake.lock` | `plugins/artagon-harness-eval/nix/harness-eval/flake.lock.in` |

## Why Clean Greenfield Over `git subtree split`

Pre-extraction evaluation history in `artagon-scripts` spanned four separate trees (`plugins/artagon-harness-eval/`, `scripts/skill_eval/`, `scripts/lib/skill_experiment_*`, and root `nix/`). A `git subtree split` on `plugins/artagon-harness-eval/` would drop half of the evaluation commit history while permanently importing monorepo APM checksum churn and legacy god-files. Pre-extraction history remains intact in `artagon/artagon-scripts` at commit `4bc7df28c98704b344c91fce2c710d182a72144b`.
