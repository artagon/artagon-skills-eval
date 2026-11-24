---
name: shell-linting
description: >-
  Configures and troubleshoots shell static analysis with ShellCheck, shfmt, and reviewed Shellharden suggestions for declared targets. Use for lint or formatter work; not for dialect selection alone.
license: MIT
compatibility: "Requires selected ShellCheck, shfmt and optionally Shellharden binaries. Native Zsh has no ShellCheck lane; shfmt 3.13+ Zsh support is incomplete. No MCP server or network is required for local checks."
allowed-tools: Read Write Edit Glob Grep Bash
metadata:
  version: "1.2.0"
  status: experimental
  researched-tools: "shellcheck=0.11.0 shfmt=3.14.1 shellharden=4.3.2"
  upstream: "wshobson/agents@c15b108 (MIT), locally corrected and extended"
---

# Shell linting

Skill marker: `artagon-shell/shell-linting/v1`.

## Choose the supported checks

Read the [target contract](references/target-contract.md), inspect existing
configuration and inventory targets by launch/source role. Include extensionless
scripts, `.bash`, `.zsh` and sourced libraries. An extension alone is not a
dialect contract; a project-wide `shell=bash` can hide POSIX issues.

| Target | Static lane | Limit |
| --- | --- | --- |
| Bash | ShellCheck bash; shfmt `-ln bash`; reviewed Shellharden suggestions | No exact Bash minimum-version validation |
| POSIX sh | ShellCheck sh/dash as declared; shfmt `-ln posix` | No POSIX 2017/2024 edition selector |
| Native Zsh | `zsh -n`; supported shfmt `-ln zsh` constructs; native review | No ShellCheck dialect; formatter support remains incomplete |

shfmt added incomplete Zsh support in 3.13.0; the researched 3.14.1 continues
fixing it. Do not relabel native Zsh as Bash to produce a green result.
Shellharden is Bash-focused and does not prove POSIX or native-Zsh compatibility.

## Check and diff before writes

For an explicitly Bash target:

```bash
shfmt -ln bash -d -i 2 -ci -bn -- script.sh
shellharden --check -- script.sh
shellcheck --shell=bash --format=json1 --severity=info -x -- script.sh
```

Keep each exit status. Missing tools, parse failures and unsupported targets are
not clean checks. Shellharden 4.3.2 uses status 2 for suggested changes; distinguish
findings from tool errors at the integration boundary.

SC2086 is **info**, so `--severity=warning` omits that common quoting diagnostic.
Use `info` when quoting coverage is intended, and document any stricter or
narrower policy. Optional checks need an explicit policy such as `enable=all`.
Read [SC codes](references/sc-codes.md) for targeted explanations.

## Configuration and fixes

Use per-file dialect declarations or explicit commands for mixed trees.
Enable external-source analysis only within the reviewed source scope.
Split declaration and substitution (SC2155); review SC2310/SC2311/SC2312
rather than disabling them by default. `cmd; rc=$?` is not an errexit-safe
general fix; conditional functions need explicit internal status propagation.

`json1` contains structured locations and applicable fix replacements.
ShellCheck also emits proposed patches with `-f diff`; applying them is a
separate authorized mutation. Review the patch and behavior after any change.

shfmt `-d` proposes formatting; `-w` writes. Inspect EditorConfig and explicit
flags together. Simplification (`-s`, and `-mn` which implies it) requires
semantic review. Formatting acceptance is not runtime proof.

Shellharden `--check` and `--transform` support review before `--replace`.
A suggestion may break intentional splitting/globbing. Refactor argv lists to
the target language's argument-vector form or document a narrow suppression.
See [Shellharden](references/shellharden.md) and
[CI integration](references/ci-integration.md) for filename-safe discovery.

## Related workflows and sources

- [Authoring](../shell-authoring/guide.md): code and style.
- [Defensive coding](../../../SKILL.md): runtime failure paths.
- [Testing](../shell-testing/guide.md): actual target execution.
- [Gate](../shell-gate/guide.md): packaged aggregation and advisory screening.

Sources: [ShellCheck 0.11.0 manual](https://github.com/koalaman/shellcheck/blob/v0.11.0/shellcheck.1.md),
[shfmt 3.14.1 manual](https://github.com/mvdan/sh/blob/v3.14.1/cmd/shfmt/shfmt.1.scd),
[Shellharden 4.3.2](https://github.com/anordal/shellharden/blob/v4.3.2/README.md).
Check/diff-first configuration also adapts the inspected abdullahkhawer source;
pins and candidate boundaries are attributed in the target contract.

## Harmless invocation

`shell-linting explain the existing configuration and propose checks`.
Read configuration and report supported lanes; do not rewrite files or install
tools. Report `mutations=none`.

## Output contract

Report target inventory, binary versions/configuration, per-tool commands and
exit statuses, diagnostics and proposed fixes, unsupported lanes and unverified
runtime/utility contracts. Never treat a missing-tool JSON result as a pass.
