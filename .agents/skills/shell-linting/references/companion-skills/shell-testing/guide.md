---
name: shell-testing
description: >-
  Writes, reviews, and runs shell behavior tests with Bats or ShellSpec for declared interpreters and utility platforms. Use for shell test design or execution; not for dialect selection alone.
license: Apache-2.0
compatibility: "Bats requires Bash 3.2+ as its test host. Tested programs require their declared interpreters and utilities. ShellSpec is optional for same-shell library tests; no MCP server or network is required for local tests."
allowed-tools: Read Write Edit Glob Grep Bash
metadata:
  version: "1.1.0"
  status: experimental
  default-framework: "bats-core"
  alternate-framework: "shellspec"
---

# Shell testing

Skill marker: `artagon-shell/shell-testing/v1`.

## Target and harness are separate

Read the [target contract](references/target-contract.md). Record the program's
dialect/edition, minimum interpreter, executable/source/interactive role and
utility implementations separately from the test harness.

Bats 1.14.0 runs on Bash 3.2+ and can test any UNIX program. Use it for CLI
contracts under explicit `dash`, BusyBox ash, Bash or native Zsh invocations.
A Bash-hosted harness does not make the program Bash-only. Do not source a
native-Zsh or POSIX-target library into Bash and call it target-shell evidence.

ShellSpec 0.28.1 is optional when same-shell library inclusion, BDD or its mocking
model fits the task. Select its runner explicitly. It is not a prerequisite
merely because a program targets another shell. See
[Bats patterns](references/bats-patterns.md) and
[ShellSpec selection](references/shellspec-deep-dive.md).

## CLI test shape

```bats
#!/usr/bin/env bats

@test "POSIX program rejects missing input under dash" {
  run dash scripts/example.sh --input "$BATS_TEST_TMPDIR/missing"
  [ "$status" -eq 2 ]
  [[ "$output" == *"not found"* ]]
}
```

Use the repository's established helpers. Isolate fixtures in
`BATS_TEST_TMPDIR`; use PATH stubs or test doubles for external side effects.
Test the CLI contract through argv, exact status, stdout/stderr and filesystem
results. Source internals only for a library contract.

## Compatibility matrix

| Contract | Evidence needed |
| --- | --- |
| Bash 3.2 | Actual 3.2 and current interpreter; no substitute with generic Bash lint |
| Bash 4.4+ | Actual minimum/current interpreters and required feature checks |
| POSIX 2017 | Named dash/ash/BSD sh implementations and declared utility floors |
| POSIX 2024 | Actual implementations of required 2024 features, including pipefail if used |
| Native Zsh | Actual minimum/current Zsh, option state and script/autoload/startup context |
| Sourced library | Source into the intended caller; assert options, traps, IFS, cwd and environment |

Missing tools or matrix cells remain unverified. `bash --posix` or Zsh
sh-emulation may be an additional lane; neither stands in for all POSIX shells.

## Meaningful failure cases

- Conditional-function invocation, pipeline status, command substitution,
  declaration/status masking and cleanup preserving the original failure.
- Signals, owned-child waiting, retries, partial writes and lock ownership.
- Empty/unset values and arrays; spaces, newlines, globs and leading dashes in
  paths; zero-file discovery and stdout/stderr contracts.
- GNU/BSD/BusyBox utilities as a separate matrix. An interpreter switch does not
  test `sed -i`, `stat`, `date`, `realpath` or xargs behavior.
- Source versus execute mode. Native-Zsh interactive completion/ZLE work may need
  PTY tests and startup-file context rather than a noninteractive syntax check.

Use inert fixtures for destructive paths. Keep production fail-closed behavior;
do not weaken expectations or skip failing cases to report a pass.

## Related workflows and sources

- [Authoring](../shell-authoring/guide.md): code changes and style.
- [Defensive coding](../shell-defensive/guide.md): failure contracts.
- [Linting](../../../SKILL.md): static tool coverage.
- [Gate](../shell-gate/guide.md): packaged checks.

Sources: [Bats 1.14.0 introduction](https://github.com/bats-core/bats-core/blob/v1.14.0/docs/source/index.rst),
[ShellSpec 0.28.1](https://github.com/shellspec/shellspec/blob/0.28.1/README.md).
Bats reference lineage: `wshobson/agents@c15b108`, MIT; locally corrected.
Pinned compatibility and candidate sources are attributed in the target contract.

## Harmless invocation

`shell-testing design inert tests for a supplied POSIX 2017 CLI`.
Return cases and interpreter requirements without executing the program;
report `mutations=none` and `tests_run=none`.

## Output contract

Report test files, target/harness identities, exact commands actually executed,
pass/fail/skip counts, missing matrix cells and remaining risk. Eval sources are
plans until model invocations and their evidence are recorded.
