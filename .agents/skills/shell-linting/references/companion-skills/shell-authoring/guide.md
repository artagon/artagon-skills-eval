---
name: shell-authoring
description: >-
  Authors, reviews, and refactors shell scripts using a declared Bash, POSIX, or native Zsh target and Google style adaptations. Use for shell code changes; not for dialect selection alone.
license: Apache-2.0
compatibility: "Requires the target interpreter and project-approved syntax, lint, and test tools. No MCP server or network access is required for local work; current external API facts need documentation lookup."
allowed-tools: Read Write Edit Glob Grep Bash
metadata:
  version: "1.1.0"
  status: experimental
  canonical-style: "Google Shell Style Guide with explicit dialect adaptations"
  canonical-rules: "ShellCheck SC-codes where supported"
---

# Shell authoring

Skill marker: `artagon-shell/shell-authoring/v1`.

## Target before recipe

Declare dialect/standards edition, minimum version, executable versus sourced or
interactive role, and OS/utility dependencies. Use
[target contract](references/target-contract.md). Pair this workflow with
`shell-bash`, `shell-posix`, or `shell-zsh` for language selection; a selector
alone does not authorize rewriting a script.

## Author or review

1. Inspect instructions, launch contract, public names and callers before edits.
   Preserve existing APIs, paths and unrelated work.
2. Apply the declared language rules. Bash `[[ ]]`, arrays, `local`, ERR traps
   and `inherit_errexit` are not universal shell syntax.
3. Preserve argv boundaries with quoted expansions and `"$@"`; use Bash arrays
   for argument vectors, POSIX positional parameters, and native Zsh expansion
   rules. Do not parse `ls` or command output into filenames by word splitting.
4. Check critical command statuses explicitly. Split declaration from command
   substitution; a declaration builtin can hide the substitution's failure.
   Functions invoked in conditions must propagate internal failures explicitly.
5. Keep stdout for data and diagnostics on stderr. Check `cd`, validate required
   arguments before `shift`, reject unknown options, and use predictable `printf`.
6. Verify the actual interpreter floor, intended source/execute mode and utility
   platforms. Static checks alone do not establish runtime compatibility.

## Google baseline and Artagon adaptations

Google's Bash guide specifies `#!/bin/bash`, two-space indentation, an 80-column
limit with exceptions, lowercase underscore function/variable names, namespaced
library functions, uppercase constants/exports and non-executable `.sh`
libraries. Its 100-line advice concerns language choice, not line width or an
automatic rewrite order. Review complexity and the migration scope before
choosing another language.

Artagon may use `#!/usr/bin/env bash` for a declared PATH launch contract.
That does not select a version or supply GNU utilities. New Bash library
functions use `namespace::lower_snake_case`; new plain functions use
`lower_snake_case`. POSIX function names use portable Names. Declare file
constants near the top with `readonly`; distinguish local style from Google's
exact wording. Preserve established public names.

## Failure policy

Use the project's strict options for compatible Bash executables. Bash 4.4+
can add `shopt -s inherit_errexit`; Bash 3.2 requires explicit propagation.
Do not paste a global `set`/`shopt`/IFS/trap preamble into sourced libraries or
native Zsh configuration. Preserve the caller-state contract.

Neither `-e` nor ERR traps catches every failure. `cmd; rc=$?` may never reach
the assignment under active errexit. For a status-handled simple command use
`if cmd; then ...; else rc=$?; ...; fi`. If `cmd` is a function, check and
return critical failures inside it because conditional invocation suppresses
errexit there. Do not remove fail-closed behavior to make a fixture pass.

## Related workflows and sources

- [Defensive coding](../shell-defensive/guide.md): failure paths, cleanup, locking and risky file operations.
- [Testing](../shell-testing/guide.md): explicit interpreter and utility matrix.
- [Linting](../../../SKILL.md): supported static tools and reviewed fixes.
- [Gate](../shell-gate/guide.md): packaged checks and advisory screening.

Sources: [Google Shell Style](https://google.github.io/styleguide/shellguide.html),
[ShellCheck wiki](https://www.shellcheck.net/wiki/), and
[BashPitfalls](https://mywiki.wooledge.org/BashPitfalls). Compatibility contracts
adapt the inspected sjinks and posidoni sources attributed in the target contract;
examples are local adaptations, not a claim of upstream runtime acceptance.

## Harmless invocation

`shell-authoring review a supplied Bash 3.2 function without edits`.
Return source-grounded findings and proposed fixes; report `mutations=none`.

## Output contract

Report the target contract, changed files or exact findings, checks actually run,
unverified matrix cells, and remaining risks. Cite applicable SC codes only for
dialects the analyzer supports.
