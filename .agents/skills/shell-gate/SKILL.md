---
name: shell-gate
description: >-
  Uses the packaged shell quality gate for declared script targets and advisory command screening. Use for gate checks or explicit project integration; not for automatic hook installation.
license: Apache-2.0
compatibility: "Requires the packaged Bash gate and its documented host version plus supported target analyzers. Native Zsh has no ShellCheck lane. No MCP server or network is required for local checks; hook integration needs current client documentation."
allowed-tools: Read Write Edit Glob Grep Bash
metadata:
  version: "1.1.0"
  status: experimental
  ships-executable: scripts/shell-gate.sh
---

# Shell quality gate

Skill marker: `artagon-shell/shell-gate/v1`.

## Establish the gate contract

Read the [target contract](references/target-contract.md) and the packaged
[gate script](scripts/shell-gate.sh) before invoking it. Separate the gate's
Bash host/version requirement from the checked file's language/version.
Do not claim that a Bash-hosted tool proves a Bash 3.2, POSIX edition or native
Zsh target compatible.

```bash
plugins/artagon-shell/skills/shell-gate/scripts/shell-gate.sh path/to/script.sh
```

The gate host requires Bash 4.4+. Select targets with
`--shell auto|bash|sh|zsh`; a recognized shebang wins auto detection. Without a
shebang, `.sh` defaults to POSIX sh; use `--shell bash` for sourced Bash files.
Bash runs explicit Bash shfmt, Shellharden check, and Bash ShellCheck at info
severity. sh runs POSIX shfmt and sh ShellCheck; Shellharden is Bash-only.
Native Zsh, Fish, Nushell and Ksh are unsupported and return failure after
command screening. The gate does not execute target files.

Exit 0 means the selected checks are clean; 1 includes findings, missing files,
missing tools, parse errors and unsupported targets; 2 denotes denied command
screening. Hook command screening needs jq, not the file analyzers. Keep these
outcomes visible and use current help for invocation details.

## What a pass can establish

- shfmt diff checks formatting in a supported dialect; incomplete native-Zsh
  parser coverage cannot certify arbitrary Zsh.
- Shellharden check mode proposes quoting changes under Bash-focused assumptions.
- ShellCheck supports sh/bash/dash/ksh/busybox, not native Zsh. Its severity
  threshold matters: SC2086 is informational, omitted by warning-only runs.
- Current ShellCheck has some POSIX-2024 rules and no exact Bash-version or
  standards-edition selector. Minimum-interpreter and utility-platform behavior
  requires the test matrix.

Report the actual tool versions, configured severity and selected lanes. Do not
repeat an old self-test claim unless this version was actually run.

## Command screening and integration

Command-pattern screening is an advisory fast path. It cannot resolve all shell
expansions, wrappers, dynamic commands, symlink races or process effects.
An OS sandbox is the isolation boundary when one is required by the task.

Hook installation, permission changes and sandbox configuration require an
explicit project task. Inspect existing project configuration and current
provider documentation first. Do not infer hook support from historical snippets
or mutate user/global configuration as a side effect of linting.

Read only the matching reference:
- [Project instruction block](references/agents-md-template.md): dialect-aware local policy.
- [Hook integration](references/hook-configs.md): historical examples and verification boundary.
- [Sandbox examples](references/sandbox-ralph.md): bounded isolation design.
- [Gemini mutation examples](references/gemini-hook-mutation-patterns.md): review before any rewriting.
- [Scanner limits](references/scanner-rebuttals.md): findings are distinct from security containment.

## Related workflows and sources

- [Authoring](references/companion-skills/shell-authoring/guide.md): scripts and style.
- [Defensive coding](references/companion-skills/shell-defensive/guide.md): runtime safety.
- [Testing](references/companion-skills/shell-testing/guide.md): behavior and compatibility.
- [Linting](references/companion-skills/shell-linting/guide.md): analyzer configuration.

Historical integration research: `docs/shell-skills-research.md` §§4,6.
Current analyzer boundaries use the primary pinned tool sources in the target
contract. Historical hook schemas and sandbox recipes are not verified-current
client configuration.

## Harmless invocation

`shell-gate explain supported profiles and failure statuses without installing hooks`.
Inspect the shipped artifact and report its actual contract; report
`mutations=none`.

## Output contract

Report checked target/role, gate host and analyzer identities, commands/exit
statuses actually observed, findings, unsupported lanes and residual risk.
Separate static quality, runtime compatibility and OS isolation evidence.
