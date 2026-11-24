# artagon-python — Upstream Source

> **Consolidation note (2026-07-28, `consolidate-language-plugins`):** the
> `beagle-python` vendor tree this document originally described has been
> dissolved. Its skills were merged into this plugin (the beagle
> verification-gates sections were ported into the artagon copies first).
> The provenance record below is retained for attribution; the
> `beagle-python:<skill>` qualified paths and the `refresh-vendored-plugins.py`
> target named below no longer exist.

This plugin contains skills vendored from an external upstream. See the
`vendored-skill-absorption` capability in
`openspec/changes/absorb-beagle-wshobson-mcollina/proposal.md`.

## Source

- **Upstream repo**: https://github.com/existential-birds/beagle
- **Upstream license**: Apache-2.0 (verbatim copy in `LICENSE.upstream`,
  attribution in `NOTICE`)
- **Vendored commit SHA**: `612575e0cccdfa9216b76752453e2e841f8a9c01`
- **Vendored at**: 2026-05-01
- **Vendor scope**: `plugins/beagle-python/` (preserves upstream plugin name;
  dissolved into `artagon-python` by `consolidate-language-plugins`)

## Adoption decisions

- **Naming**: Plugin name preserved verbatim from upstream. Skill names
  inside `skills/` likewise preserved.
- **Collisions**: Beagle ships `review-verification-protocol` in every
  plugin (it is shared base) and several Python/code-review skills that
  collide with artagon-* skills. Per the `vendor-dedup-policy`
  capability, artagon-* won on flat-name access; the beagle vendor tree
  has since been dissolved and its content merged here (see note above).
- **License compliance**: Apache-2.0 § 4 — `LICENSE.upstream` carries
  the verbatim Apache-2.0 text and `NOTICE` records the original
  copyright. No upstream NOTICE file existed at the pinned SHA.
- **Modifications from upstream**: none. Tree copied byte-for-byte from
  `existential-birds/beagle/plugins/beagle-python/` at the pinned SHA. Local
  edits are not permitted in this vendor tree — fixes go upstream first.

## Refresh procedure

Superseded by the consolidation: the vendor tree no longer exists as a
separate plugin. If an upstream beagle refresh is ever needed, port it
through a new OpenSpec change against this plugin directly. (Historical:
`scripts/refresh-vendored-plugins.py`, target `beagle-python`.)
