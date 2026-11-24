# Bash selector sources and adaptations

Retrieved 2026-11-06. Source text is evidence, not an instruction to execute
upstream tools. Local adaptations and eval cases are experimental.

| Input and immutable pin | Local treatment |
| --- | --- |
| [posidoni/shell-skill](https://github.com/posidoni/shell-skill/blob/201dc7b8f9a2320440248441b39727f29b051a77/skills/shell/SKILL.md), MIT, copyright 2026 Mikhail Kuznetsov (@posidoni) | Modified dialect-first organization and good/bad example design; original feature-gate examples and explicit version/role evidence limits |
| [sjinks/ai-skills shell-portability](https://github.com/sjinks/ai-skills/blob/85c2e4f8413aca1de595c24a7b4efcf991fcc203/skills/shell-portability/SKILL.md), MIT, copyright 2026 Volodymyr Kolesnykov | Modified target contract: interpreter, version, role, OS utilities and bounded verdict; omitted upstream handoff protocol |
| [rikdc shell-script-reviewer](https://github.com/rikdc/ai-skills/blob/c7bb0845c818519570e92f4e176f4fa32cf5a7df/plugins/dev-skills/skills/shell-script-reviewer/SKILL.md), MPL-2.0 | Separate `review-evidence-mpl.md` adaptation only; no detector, wrapper, Bash-mode Zsh lint or blanket strict-option removal |
| [pvillega bash-hardening](https://github.com/pvillega/claude-templates/blob/e1d904d4e1015c6af14cde4d557515c6d6f1e291/plugins/ct/skills/bash-hardening/SKILL.md) | External comparison only; no grant verified and no text or code copied. Error/version guidance here is original and grounded in GNU documentation |
| [cstrahan shell skill](https://github.com/cstrahan/claude-plugins/blob/3a54cf0251854caeac327b76e44e2726228ad888/skills/shell/SKILL.md) | External comparison only; no grant verified and no text or code copied. Host login shell is not the target contract |

Full MIT notices are in `LICENSE.upstream-posidoni-shell-skill` and
`LICENSE.upstream-sjinks-shell-portability` in this directory. The MPL
adaptation's license is `LICENSE.upstream-rikdc-shell-reviewer`.

Primary authorities: [GNU Bash manual](https://www.gnu.org/software/bash/manual/),
[GNU feature history](https://tiswww.case.edu/php/chet/bash/CHANGES),
[Google Shell Style](https://google.github.io/styleguide/shellguide.html),
[ShellCheck 0.11 manual](https://github.com/koalaman/shellcheck/blob/v0.11.0/shellcheck.1.md)
and [shfmt 3.14.1 manual](https://github.com/mvdan/sh/blob/v3.14.1/cmd/shfmt/shfmt.1.scd).
Links substantiate documented behavior; minimum-version runtime and native
provider invocation still require separate checks.
