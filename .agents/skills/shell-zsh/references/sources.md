# Native Zsh selector sources and adaptations

Retrieved 2026-11-06. The source pins are immutable. No upstream executable,
installer, semantic suite or framework hook was imported.

| Input and immutable pin | Local treatment |
| --- | --- |
| [ZaguanLabs SKILL](https://github.com/ZaguanLabs/zsh-expert-skill/blob/cf2731a05cd6c8961d13b0f3faf79c49559fad32/SKILL.md), Apache-2.0 | Modified context contract, option/caller-state review, native-topic routing and evidence classes in the selector and `zsh-profiles.md` |
| [ZaguanLabs version guide](https://github.com/ZaguanLabs/zsh-expert-skill/blob/cf2731a05cd6c8961d13b0f3faf79c49559fad32/references/22-version-gates.md), same pin/license | Modified version/capability distinction and parse-time isolation; corrected real-time signals, `kill -q`/`-L` and `_as_if` to 5.9.1 using official release notes |
| [posidoni/shell-skill](https://github.com/posidoni/shell-skill/blob/201dc7b8f9a2320440248441b39727f29b051a77/skills/shell/SKILL.md), MIT, copyright 2026 Mikhail Kuznetsov (@posidoni) | Modified dialect/example organization; no Bash-run example is presented as native Zsh proof |
| [sjinks shell-portability](https://github.com/sjinks/ai-skills/blob/85c2e4f8413aca1de595c24a7b4efcf991fcc203/skills/shell-portability/SKILL.md), MIT, copyright 2026 Volodymyr Kolesnykov | Modified separation of interpreter and OS utility dependencies |
| [rikdc shell-script-reviewer](https://github.com/rikdc/ai-skills/blob/c7bb0845c818519570e92f4e176f4fa32cf5a7df/plugins/dev-skills/skills/shell-script-reviewer/SKILL.md), MPL-2.0 | Separate `review-evidence-mpl.md` adaptation only; rejects Bash-mode ShellCheck as native Zsh validation |

Full notices and license text are in `NOTICE.adoption`,
`LICENSE.upstream-zaguan-zsh-expert`, `LICENSE.upstream-posidoni-shell-skill`,
`LICENSE.upstream-sjinks-shell-portability` and
`LICENSE.upstream-rikdc-shell-reviewer` in this directory. The upstream
Apache license contains the standard template copyright placeholder; no
additional upstream notice file was established by the research inventory.

The pinned Zaguan SKILL, version guide and license were read through native
DuckDuckGo public fetch for this adaptation. Its extracted text is not a
byte-exact upstream archive. The recorded SKILL blob identity remains the
research pin; no new digest is falsely assigned to extracted prose.

Primary authorities: [official Zsh release notes](https://zsh.sourceforge.io/releases.html),
[release manual](https://zsh.sourceforge.io/Doc/Release/),
[shfmt 3.14.1 manual](https://github.com/mvdan/sh/blob/v3.14.1/cmd/shfmt/shfmt.1.scd)
and [ShellCheck 0.11 manual](https://github.com/koalaman/shellcheck/blob/v0.11.0/shellcheck.1.md).
Upstream's reported bounded 5.9.2 Linux tests are not fresh Artagon results,
older-version proof or PTY acceptance for an arbitrary plugin.
