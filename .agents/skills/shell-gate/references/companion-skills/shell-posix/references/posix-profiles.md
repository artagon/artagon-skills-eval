# POSIX editions, implementations and utilities

Modified adaptation of the target-contract approach in sjinks/ai-skills
and the dialect/example organization in posidoni/shell-skill, with original
Artagon standards corrections. The source card identifies pins and MIT
notices. This file supplies no runtime compatibility guarantee.

| Requirement | POSIX.1-2017 / Issue 7 | POSIX.1-2024 / Issue 8 |
| --- | --- | --- |
| Pipeline status | No standardized `pipefail` | `pipefail` is standardized |
| `readonly` | `readonly name[=word]...` and `readonly -p` are standard | Standard; distinguish implementation-only flags |
| Function names | Portable Name identifiers | Portable Name identifiers; `namespace::name` is an extension |
| Arrays, `[[ ]]`, `source`, `local`, `shopt` | Do not assume them | Do not treat them as a portable sh baseline |
| NUL file traversal | Do not assume `find -print0` or `xargs -0` as standard | `find -print0` and `xargs -0` are standard |
| Other utility additions | Do not assume `sed -E`, `readlink` or `realpath` commands from this edition | Those forms/utilities are standard; `readlink -f` remains outside the standard |

The primary shell-language authorities are
[Issue 7](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
and [Issue 8](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html).
The [Issue 8 rationale](https://pubs.opengroup.org/onlinepubs/9799919799/xrat/V4_xcu_chap01.html)
records the pipefail addition. Standardization does not prove that any
particular deployed dash, ash or BusyBox build implements a feature.

## Source and naming boundaries

Use portable names such as `cache_load`, rather than importing Bash
`cache::load` names into a new portable API. Preserve an existing external
API and report its portability constraint rather than silently renaming it.
For sourced files use `. file` and the intended caller shell. A shebang
does not change the interpreter when a file is sourced. POSIX leaves the
handling of a command file beginning `#!` unspecified; `/bin/sh` is a
deployment convention, not a universal path guaranteed by POSIX.

Do not transplant Bash strict-mode, array or NUL-reading recipes into this
profile. `set`, traps, IFS and directory changes in a sourced file affect
its caller. Record and test the ownership/restoration contract. Explicit
handling of critical failures is still required; `-e` has context-dependent
exceptions. A `pipefail` probe that simply turns it off when absent loses
required detection and is not a valid compatibility fix.

## Utility matrix

Name the actual implementation and version for each dependency. Record
BusyBox build/applet availability as well as the BusyBox version. Shell
selection says nothing about whether `stat`, `sed`, `find`, `date`,
`readlink`, `mktemp` or `getopt` comes from GNU, FreeBSD, macOS or BusyBox.

- `sed -i` is not a POSIX interface and its argument rules differ even
  among BSD implementations. Prefer a reviewed temporary-output and
  replacement flow when in-place editing is necessary.
- GNU `stat -c` is not interchangeable with macOS/FreeBSD `stat -f`.
- `date` parsing flags, `readlink -f`, `mktemp` templates and timeout tools
  need implementation-specific checks. Command presence alone is not a
  semantic check.
- Treat locale as part of the contract for matching, sorting and byte
  operations. An `LC_ALL=C` override must be scoped when the caller owns
  locale and must suit the intended data semantics.
- If filenames may contain newlines, avoid newline-delimited shell loops.
  Under a 2017 target consider `find ... -exec command {} +` where its argv
  contract fits, rather than assuming newer NUL options exist.

## Validation and verdict

Run the actual minimum dash/ash/other interpreter and utility environment
for the claimed deployment cells. Parse checks and `shellcheck -s sh`,
`shfmt -ln posix -d`, or checkbashisms are static evidence only. Inspected
ShellCheck interfaces do not select a POSIX edition; current diagnostics
can follow 2024 and miss a 2017-only requirement.

Bats can test any executable by invoking its interpreter explicitly;
running a test in Bash or sourcing a sh file into Bash does not establish
dash or ash behavior. A same-shell runner such as ShellSpec is an optional
choice for libraries. Exercise relevant failure paths and caller state
under each target. Missing tools, unavailable platforms and skipped cells
remain missing coverage, never successful conformance evidence.

A useful verdict is `compatible for tested cells`, `incompatible` with a
concrete construct/utility conflict, or `unverified` with missing cells.
Do not broaden a bounded test result into POSIX certification.
