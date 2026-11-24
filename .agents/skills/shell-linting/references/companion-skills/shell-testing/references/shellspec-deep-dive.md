# ShellSpec selection and same-shell tests

ShellSpec is optional, useful when its same-shell library inclusion, BDD or
mocking model fits the contract. ShellSpec 0.28.1 documents multiple runners.
Bats 1.14.0 runs its harness on Bash 3.2+ and can explicitly execute any UNIX
program. Neither tool is required solely by the tested program's dialect.

## Choose by the behavior under test

| Need | Bats | ShellSpec |
| --- | --- | --- |
| CLI argv/status/output/files | Explicitly invoke the target program/interpreter | Explicit program invocation |
| Sourced library caller state | Launch target shell and source inside it | Select target runner and Include |
| Native Zsh script | Execute actual Zsh | Select Zsh runner |
| Mocking | PATH stubs or approved helpers | Use documented Mock/Intercept facilities |
| PTY/startup/ZLE behavior | Add an appropriate PTY harness | Same requirement; a runner switch is insufficient |

Do not source POSIX or native-Zsh code into Bash and report target compatibility.
Select actual minimum/current interpreter paths and record versions. Bash POSIX
mode and Zsh sh-emulation are separate profiles, not substitutes for named sh
implementations or standards editions.

## Runner examples

```sh
shellspec --shell /bin/bash spec/
shellspec --shell dash spec/
shellspec --shell zsh spec/
```

These are proposed commands, not recorded runs. Check runner syntax, availability
and pinned framework behavior before use. A generic `sh` command alone does not
identify its implementation or POSIX edition. BusyBox multi-call invocation must
be configured and verified rather than assuming `busybox` alone means ash.

Keep each spec valid in its declared runner. Shared POSIX specs may run across
several shells; a native-Zsh autoload spec need not parse as Bash.

## Library and failure cases

Test options, traps, IFS, cwd, environment, positional parameters and repeated
sourcing according to the library's stated contract. For Zsh functions,
`emulate -L zsh` localizes documented function state, not all process effects.

Test conditional functions, pipeline failures, substitution failures, masked
declaration status, cleanup failure and signals. Preserve the production
failure policy. Framework subshells, mocks and sandbox features are not proof
of OS isolation or actual deployment utility availability.

## Installation and evidence

Use the consuming project's approved dependency process and pin the version.
Do not pipe an unreviewed network installer into a shell, install globally or
assume an optional framework must be installed. If ShellSpec is absent, report
that fact and use an available appropriate harness or leave the lane unverified.

Capture runner identity, exact command, result counts and missing dependencies.
A written spec or a clean parse is not an executed behavior result.

## Sources

[ShellSpec 0.28.1 README](https://github.com/shellspec/shellspec/blob/0.28.1/README.md)
and [Bats 1.14.0 introduction](https://github.com/bats-core/bats-core/blob/v1.14.0/docs/source/index.rst).
Locally corrected from `docs/shell-skills-research.md` §1; historical framework
maintenance labels are not current compatibility evidence.
