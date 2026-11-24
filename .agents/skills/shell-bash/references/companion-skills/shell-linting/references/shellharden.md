# Shellharden: reviewed Bash quoting suggestions

Shellharden 4.3.2 is Bash-focused. It is useful for quoting and backtick
modernization, with explicit review of changed splitting/globbing behavior.
It is not a native-Zsh analyzer or a POSIX-edition compatibility gate.
ShellCheck can also emit applicable fix patches; Shellharden is not the only
tool capable of proposed rewrites.

## Review before replacement

```bash
shellharden --check -- script.sh
shellharden --transform -- script.sh > script.transformed.sh
diff -u -- script.sh script.transformed.sh
```

The first command is read-only; in 4.3.2 status 2 means suggestions exist.
The second writes a separate review artifact. Run it only when an artifact
write is in scope. `--replace` mutates the source and needs authorized edits,
diff review and relevant behavior tests.

A suggestion is not proof of a bug. Deliberate field splitting or globbing may
be part of the API. Preserve the argument contract before transforming:

```bash
# Bash argv vector; available on Bash 3.2.
flags=(--verbose --color=auto)
some_command "${flags[@]}" "argument with spaces"
```

POSIX sh uses positional parameters instead of arrays. Native Zsh has its own
expansion rules. Do not automatically parse a free-form environment string as
shell syntax or use eval. If deliberate splitting remains necessary, document
the exact separators, glob policy and trusted input contract with a narrow
ShellCheck suppression.

## Brownfield adoption

1. Inspect existing configuration and declare a Bash-only file inventory.
2. Invoke `--check -- "$file"` for each preserved argv entry. Use a NUL manifest
   or an explicit array; never `shellharden $(git ls-files ...)`.
3. Review suggestions, refactor argument vectors and test intentional splitting.
4. Apply approved changes in small coherent patches and run matched static and
   behavior checks. Do not blanket-rewrite unrelated files.
5. Add a check-mode integration with documented diagnostic-versus-tool-error
   exit handling.

An empty inventory must run no commands and be reported as zero checked files.
Keep discovery errors visible. NUL delimiters alone do not establish portable
xargs empty-input behavior.

Shellharden does not replace explicit status handling, `cd` checks, failure
tests or source-mode state review. A suggested transform cannot establish
runtime safety.

## Sources

[Shellharden 4.3.2 README](https://github.com/anordal/shellharden/blob/v4.3.2/README.md)
and [CLI exit handling](https://github.com/anordal/shellharden/blob/v4.3.2/src/main.rs);
[ShellCheck 0.11.0 fix output](https://github.com/koalaman/shellcheck/blob/v0.11.0/shellcheck.1.md).
Locally corrected from `docs/shell-skills-research.md` §3.
