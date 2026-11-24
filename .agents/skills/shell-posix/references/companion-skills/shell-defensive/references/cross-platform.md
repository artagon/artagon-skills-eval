# Shell syntax and utility platforms

Declare interpreter/version, source/execute role and utility implementations as
separate contracts. `#!/usr/bin/env bash` finds Bash on PATH; it does not select
a minimum version or install GNU utilities. Google's exact baseline is
`#!/bin/bash`; a PATH shebang is a local deployment choice.

## Utility differences

| Operation | GNU example | FreeBSD/macOS family example | Contract |
| --- | --- | --- | --- |
| sed in-place edit | `sed -i 's/a/b/' file` | `sed -i '' 's/a/b/' file` | `-i` is not POSIX; BSD variants differ too |
| Date arithmetic | `date -d '5 days ago'` | `date -v-5d` | Declare exact implementation |
| Metadata | `stat -c %s file` | `stat -f %z file` | Same flag may mean different operations |
| Final symlink | `readlink -f` or realpath | Availability/version varies | Require an actual compatible resolver |
| Empty xargs input | `-r` prevents execution | Defaults/flags vary by version | Test emptiness or use find -exec |
| File lists | find `-print0`, xargs `-0` | Available on many deployed tools | POSIX 2024 additions; not required by 2017 |

The Open Group standardized realpath/readlink utilities, find `-print0` and
xargs `-0/-r` in 2024. It did not standardize `readlink -f`.
Choosing POSIX 2024 does not supply the required utility versions.

## Physical parent is not final-target canonicalization

`(cd -P -- "$(dirname -- "$path")" && pwd -P)` resolves the parent directory,
not the final path component. Appending `basename` still leaves a final symlink
unresolved. Never use that as a security-equivalent fallback for realpath.
If final-target resolution is required, declare and check a compatible resolver
or fail closed. Keep path ownership, authorized roots and TOCTOU exposure
separate; string canonicalization is not a filesystem confinement boundary.

## Filename and empty-input behavior

For a POSIX-2017-compatible utility baseline, `find -exec ... {} +` preserves
each pathname as an argument and does not invoke the utility for an empty set:

```sh
find . -type f -name '*.log' -exec compress {} +
```

`compress` is an example dependency and the command recurses deliberately.
Do not label nonstandard `-maxdepth`, Bash process substitution or
`read -d` as universal POSIX-2017 constructs. Where a Bash NUL loop is chosen,
its producer's exit status must be checked independently of process substitution.

`find ... -print0 | xargs -0 command` preserves delimiters where those flags
exist, but does not by itself prevent invocation on zero input on every host.
Use a supported `-r`, explicit empty-list handling, or `find -exec` according
to the declared utility contract.

## Output and file updates

Use `printf '%s\n' "$value"` for data. POSIX echo behavior is implementation
defined when the first operand is `-n` or an operand contains backslashes;
some implementations interpret escapes. Bash `printf %q` is not POSIX.

Temporary-file-plus-rename edits must check every status, use a unique private
temporary file on the target filesystem, and preserve required mode/ownership.
A fixed `file.tmp` is collision-prone. Rename atomicity does not imply crash
durability or correct producer completion.

## Platform detection and line endings

Prefer feature/dependency checks over inferring every utility from `uname`.
GNU/Linux can use BusyBox utilities. Do not mutate Git configuration to fix
line endings without a project task; a reviewed `.gitattributes` policy can
cover `*.sh`, `*.bash`, `*.zsh` and named extensionless scripts.

## Sources

[POSIX 2024 utilities](https://pubs.opengroup.org/onlinepubs/9799919799/idx/utilities.html),
[GNU sed options](https://www.gnu.org/software/sed/manual/html_node/Command_002dLine-Options.html),
[FreeBSD sed](https://man.freebsd.org/cgi/man.cgi?query=sed&sektion=1&format=ascii),
[GNU stat](https://www.gnu.org/software/coreutils/manual/html_node/stat-invocation.html),
[FreeBSD stat](https://man.freebsd.org/cgi/man.cgi?query=stat&sektion=1&format=ascii).
Local corrections to `docs/shell-skills-research.md` §2, informed by the
inspected sjinks MIT portability contract.
