# POSIX selector sources and adaptations

Retrieved 2026-11-06. These inputs are source evidence. No upstream tool,
example suite or installer was executed or bundled.

| Input and immutable pin | Local treatment |
| --- | --- |
| [sjinks/ai-skills shell-portability](https://github.com/sjinks/ai-skills/blob/85c2e4f8413aca1de595c24a7b4efcf991fcc203/skills/shell-portability/SKILL.md), MIT, copyright 2026 Volodymyr Kolesnykov | Modified interpreter/version/OS target contract and explicit portability verdict; retained 2017 as a stated conservative assumption and added a separate 2024 profile |
| [posidoni/shell-skill](https://github.com/posidoni/shell-skill/blob/201dc7b8f9a2320440248441b39727f29b051a77/skills/shell/SKILL.md), MIT, copyright 2026 Mikhail Kuznetsov (@posidoni) | Modified dialect/example organization; replaced Bash-only execution assumptions with native dash/ash and utility cells |
| [rikdc shell-script-reviewer](https://github.com/rikdc/ai-skills/blob/c7bb0845c818519570e92f4e176f4fa32cf5a7df/plugins/dev-skills/skills/shell-script-reviewer/SKILL.md), MPL-2.0 | Separate `review-evidence-mpl.md` adaptation only; no wrappers, auto-fixes or upstream strict-mode policy |
| [agiacalone/unix-conventions](https://github.com/agiacalone/unix-conventions/blob/480bfcc0737622727d108ef96de8b13147c4ba9e/SKILL.md), GPL-3.0 repository evidence | External comparison only pending per-file provenance for its mixed-source bundle. No text or code copied; local standards guidance comes from official POSIX sources |
| [GitHub awesome-copilot instructions](https://github.com/github/awesome-copilot/blob/797337f33f73e35d08d82f840e21c4b8c4932d88/instructions/shell.instructions.md), MIT | Reference comparison, not another skill or a copied instruction file. Local dialect selection covers `.zsh` and extensionless files by invocation/contract rather than an extension-only glob |

Full MIT notices are in `LICENSE.upstream-sjinks-shell-portability` and
`LICENSE.upstream-posidoni-shell-skill` in this directory. The isolated MPL
adaptation uses `LICENSE.upstream-rikdc-shell-reviewer`.

Primary authorities: POSIX
[2017 shell language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html),
[2024 shell language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html),
[2024 utilities](https://pubs.opengroup.org/onlinepubs/9799919799/idx/utilities.html),
[ShellCheck 0.11 manual](https://github.com/koalaman/shellcheck/blob/v0.11.0/shellcheck.1.md)
and [shfmt 3.14.1 manual](https://github.com/mvdan/sh/blob/v3.14.1/cmd/shfmt/shfmt.1.scd).
The standards do not establish that a particular deployed shell/build
implements every listed feature.
