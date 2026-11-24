# Canonical JSON Schemas

All 10 canonical Draft 2020-12 JSON schemas live once inside the core Python package so editable `uv` checkouts, wheel builds, `importlib.resources`, and ADR-0006 `O_NOFOLLOW` Nix staging share a single source of truth with zero symlinks and zero duplicated mirrors:

- `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/cassette.schema.json`
- `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/descriptor.schema.json`
- `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/frozen-manifest.schema.json`
- `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/hook-event.schema.json`
- `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/mcp-call.schema.json`
- `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/protocol.schema.json`
- `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/shim-exec.schema.json`
- `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/skill-eval-result.schema.json`
- `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/span.schema.json`
- `packages/artagon-eval-core/src/artagon_eval_core/data/schemas/trace.schema.json`
