# ShellCheck diagnostics for supported targets

This is a selected review guide, not a complete diagnostic taxonomy. Cite each
code's canonical page at `https://www.shellcheck.net/wiki/SC<N>` and verify it
against the installed version. Some historical code labels were incorrect;
diagnostic identity and severity come from ShellCheck, not a hand-written range.

ShellCheck 0.11.0 supports sh/bash/dash/ksh/busybox, not native Zsh. Its current
sh rules include some POSIX-2024 changes and do not certify a POSIX-2017 target.
There is no exact Bash-version or standards-edition selector.

## Common diagnostics

| Code | Role | Review action |
| --- | --- | --- |
| SC2086 | info | Quote scalar arguments; preserve deliberate splitting with an explicit contract |
| SC2046 | warning | Preserve command substitution output as an argument or a real argv vector |
| SC2068 | error | Quote `"$@"` and Bash `"${array[@]}"` |
| SC2155 | warning | Separate declaration and substitution; then handle failure explicitly |
| SC2164 | warning | Check cd before dependent work |
| SC2015 | info | A && B || C is not a general if/else |
| SC2162 | info | Use read -r where backslashes must stay literal |
| SC2207 | warning | Avoid command-output splitting into arrays; mapfile needs Bash 4.0+ |
| SC2310 | optional info | Conditional function invocation suppresses errexit internally |
| SC2311 | optional info | Command substitution may clear errexit |
| SC2312 | optional info | Embedded command output can hide its status in the surrounding command |

SC2086 is omitted at `--severity=warning`. Use `--severity=info` when that
quoting coverage is intended. Optional checks need explicit enablement, such
as a reviewed `enable=all` policy. Do not disable SC2310/SC2311/SC2312 globally
to hide failure-propagation defects.

## POSIX edition and version boundaries

POSIX 2017 has no arrays, `[[ ]]`, `local`, process substitution or required
pipefail. `readonly NAME=value` is standard. POSIX 2024 standardizes pipefail;
a deployed implementation must still provide it. SC3040 explains the edition
difference. SC3036 concerns echo flags, not pipefail.

Bash `mapfile` requires 4.0+, its `-d` option and `inherit_errexit` require
4.4+. Generic Bash lint does not enforce those floors. Functions tested in
`if` or AND/OR lists must propagate each critical internal status explicitly;
`inherit_errexit` does not fix conditional contexts.

## Preserve status and argv

```bash
# Bash function: split declaration from a handled substitution.
read_value() {
  local value
  if value=$(external_reader "$1"); then
    printf '%s\n' "$value"
  else
    return "$?"
  fi
}
```

The function's internal critical command has an explicit status branch, even
when the function itself is invoked conditionally. Appending `rc=$?` after an
unguarded failure under active errexit may never execute.

For filename discovery use a checked NUL manifest, an argv array, or portable
`find -exec`; do not turn `$(git ls-files ...)` into a whitespace list.
A NUL pipeline does not alone define xargs zero-input behavior.

## Proposed fixes

```bash
shellcheck --shell=bash --format=json1 --severity=info -x -- script.sh
shellcheck --shell=bash -f diff -- script.sh
```

`json1` includes applicable replacement data. `-f diff` emits applicable
patches, not guaranteed fixes for every diagnostic. Inspect before applying;
`git apply` is a separate mutating action, followed by matched syntax and
behavior checks. Neither a proposed patch nor green lint proves runtime
compatibility.

## Sources

[ShellCheck 0.11.0 manual](https://github.com/koalaman/shellcheck/blob/v0.11.0/shellcheck.1.md),
[pinned diagnostic implementation](https://github.com/koalaman/shellcheck/blob/v0.11.0/src/ShellCheck/Analytics.hs),
[SC3040](https://www.shellcheck.net/wiki/SC3040).
Original selected ShellCheck topics from `wshobson/agents@c15b108`, MIT;
locally corrected using the 2026-11-06 primary-source research.
