# Shell target contract

Declare these four fields before choosing options, examples, tools or tests:

1. **Language:** Bash with a minimum version, POSIX sh with 2017/2024 edition,
   or native Zsh with a minimum version and option assumptions.
2. **Role:** executed script, sourced library, autoload function, interactive
   configuration, completion or ZLE widget. Record the actual invocation.
3. **State:** permitted effects on options, traps, IFS, cwd, environment, aliases,
   file descriptors and caller parameters. Source mode runs in the caller.
4. **Platform:** named OS and utility implementations/features, independently
   from shell syntax. Record absent dependencies as unsupported.

## Select a profile

| Profile | Safe selection boundary |
| --- | --- |
| Bash 3.2 | No unguarded `inherit_errexit`, associative arrays, namerefs or mapfile |
| Bash 4.4+ | `major > 4 || (major == 4 && minor >= 4)`; reject 4.3 and accept 5.0–5.3 |
| POSIX 2017 | Portable Names and `name() { ...; }`; no arrays, `[[ ]]`, `local`, `shopt` or required pipefail |
| POSIX 2024 | pipefail is standardized, but actual deployed implementations must provide required features |
| Native Zsh | Explicit version/options/context; native arrays and scalar expansion differ from Bash |
| Sourced code | Preserve declared caller state; no universal executable preamble |

`readonly NAME=value` is standard POSIX 2017. Bash-specific flags remain
extensions. POSIX 2017 does not require pipefail; 2024 does. Choosing an edition
does not upgrade the installed shell. A required failure policy must fail closed
when its dependency is unavailable; do not silently drop the check.

Google Shell Style is a Bash baseline: `#!/bin/bash`, two-space indentation,
80-column guidance with exceptions, lowercase underscore names, namespaced
library functions and uppercase constants/exports. The separate 100-line advice
concerns language choice. Artagon PATH shebangs, strict-option policies and POSIX/
Zsh adaptations must be labeled. Preserve existing APIs and filenames.

Native Zsh sh-emulation is a separate profile, not proof of POSIX conformance.
Inside a Zsh function, `emulate -L zsh` scopes options, patterns and traps to
that function; it is not a universal wrapper for startup/configuration effects.

## Tool and evidence boundary

ShellCheck 0.11.0 has no native Zsh, Bash minimum-version or POSIX-edition
selector. SC2086 is info; warning-only runs omit it. shfmt 3.13.0 introduced
incomplete Zsh support; researched 3.14.1 is still not complete validation.
Shellharden 4.3.2 is Bash-focused and proposed quoting changes need review.
Bats 1.14.0 runs on Bash 3.2+ but can execute non-Bash programs explicitly.
ShellSpec 0.28.1 can select a same-shell library runner and remains optional.

State which evidence exists: source review, tool identity/capability, syntax/
static check, or actual runtime behavior. No one class implies the next.
Compatibility claims require actual named minimum/current interpreters and
utility environments, with missing cells left visible.

## Primary sources

- [Google Shell Style](https://google.github.io/styleguide/shellguide.html)
- [POSIX 2017 shell language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
- [POSIX 2024 shell language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)
- [GNU Bash changes](https://tiswww.case.edu/php/chet/bash/CHANGES) and [set builtin](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html)
- [Zsh invocation](https://zsh.sourceforge.io/Doc/Release/Invocation.html#Compatibility), [expansion](https://zsh.sourceforge.io/Doc/Release/Expansion.html), [emulate builtin](https://zsh.sourceforge.io/Doc/Release/Shell-Builtin-Commands.html)
- [ShellCheck 0.11.0](https://github.com/koalaman/shellcheck/blob/v0.11.0/shellcheck.1.md) and [SC2086 implementation](https://github.com/koalaman/shellcheck/blob/v0.11.0/src/ShellCheck/Analytics.hs)
- [shfmt 3.14.1](https://github.com/mvdan/sh/blob/v3.14.1/cmd/shfmt/shfmt.1.scd) and [3.13.0 release](https://github.com/mvdan/sh/releases/tag/v3.13.0)
- [Shellharden 4.3.2](https://github.com/anordal/shellharden/blob/v4.3.2/README.md), [Bats 1.14.0](https://github.com/bats-core/bats-core/blob/v1.14.0/docs/source/index.rst), [ShellSpec 0.28.1](https://github.com/shellspec/shellspec/blob/0.28.1/README.md)

## Inspected skill sources and local adaptations

The 2026-11-06 research informed these local rules; code was not imported from
sources with unresolved grants. The sources do not establish local test results.

- [sjinks, MIT, 85c2e4f](https://github.com/sjinks/ai-skills/blob/85c2e4f8413aca1de595c24a7b4efcf991fcc203/skills/shell-portability/SKILL.md): explicit edition/interpreter/utility contract and portability evidence.
- [posidoni, MIT, 201dc7b](https://github.com/posidoni/shell-skill/blob/201dc7b8f9a2320440248441b39727f29b051a77/skills/shell/SKILL.md): dialect routing and paired failure/safe examples; Bash-hosted tests do not prove POSIX.
- [ZaguanLabs, Apache-2.0, cf2731a](https://github.com/ZaguanLabs/zsh-expert-skill/blob/cf2731a05cd6c8961d13b0f3faf79c49559fad32/SKILL.md): native-Zsh option/context/version contract, checked against official Zsh semantics.
- [rikdc, MPL-2.0, c7bb084](https://github.com/rikdc/ai-skills/blob/c7bb0845c818519570e92f4e176f4fa32cf5a7df/plugins/dev-skills/skills/shell-script-reviewer/SKILL.md): structured findings and missing-tool boundaries; no file content copied or Bash-mode certification of Zsh.
- [pvillega, e1d904d](https://github.com/pvillega/claude-templates/blob/e1d904d4e1015c6af14cde4d557515c6d6f1e291/plugins/ct/skills/bash-hardening/SKILL.md): hardening review questions only; grant unresolved, no code vendored.
- [abdullahkhawer, Apache-2.0, 42a412b](https://github.com/abdullahkhawer/devops-skills/blob/42a412b1a084535db514c7dc5e2f76c5d38c6bd1/skills/bash-linting/SKILL.md): inspect configuration and check/diff before fixes; broaden filename discovery.
- [wshobson, MIT, 4bde316](https://github.com/wshobson/agents/tree/4bde3168b43c0655c4d00ea2726e631719908a6d/plugins/shell-scripting): compare defensive, Bats and ShellCheck topics with existing absorbed `c15b108` lineage; correct active recipes instead of duplicate routers.
