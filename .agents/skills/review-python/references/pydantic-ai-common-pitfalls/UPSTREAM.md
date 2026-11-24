# beagle-ai — Upstream Source

This plugin is vendored from an external upstream. See the
`vendored-skill-absorption` capability in
`openspec/changes/absorb-beagle-wshobson-mcollina/proposal.md`.

## Source

- **Upstream repo**: https://github.com/existential-birds/beagle
- **Upstream license**: Apache-2.0 (verbatim copy in `LICENSE.upstream`,
  attribution in `NOTICE`)
- **Vendored commit SHA**: `612575e0cccdfa9216b76752453e2e841f8a9c01`
- **Vendored at**: 2026-05-01
- **Vendor scope**: `plugins/beagle-ai/` (preserves upstream plugin name)

## Adoption decisions

- **Naming**: Plugin name preserved verbatim from upstream. Skill names
  inside `skills/` likewise preserved.
- **Collisions**: Beagle ships `review-verification-protocol` in every
  plugin (it is shared base) and several Python/code-review skills that
  collide with artagon-* skills. Per the `vendor-dedup-policy`
  capability, artagon-* wins on flat-name access; the beagle versions
  are reachable only via `beagle-ai:<skill>` qualified paths.
- **License compliance**: Apache-2.0 § 4 — `LICENSE.upstream` carries
  the verbatim Apache-2.0 text and `NOTICE` records the original
  copyright. No upstream NOTICE file existed at the pinned SHA.
- **Modifications from upstream**: none. Tree copied byte-for-byte from
  `existential-birds/beagle/plugins/beagle-ai/` at the pinned SHA. Local
  edits are not permitted in this vendor tree — fixes go upstream first.

## Refresh procedure

See `scripts/refresh-vendored-plugins.py` (target: `beagle-ai`).
