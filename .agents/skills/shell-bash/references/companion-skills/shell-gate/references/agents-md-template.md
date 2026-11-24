# Project instructions for declared shell targets

Inspect existing instructions before proposing changes. Updating AGENTS.md or
creating client symlinks is a separate project edit, not an implicit effect of
running the quality gate. Preserve each client's current file contract and
existing user content.

## Example instruction block

```markdown
## Shell work

- Declare dialect/edition, minimum interpreter, executable/source/interactive
  role and utility implementations before choosing patterns.
- Preserve public APIs, launch paths and unrelated work.
- For new Bash code use Google style with named local adaptations:
  lower_snake_case, namespace::lower_snake_case library functions,
  UPPER_SNAKE_CASE constants/exports and readonly file constants.
- Use portable Names for POSIX function identifiers. readonly is POSIX 2017.
- Bash-only arrays, [[ ]], local, ERR traps and shopt do not belong in
  a universal .sh preamble. POSIX pipefail is edition-2024 plus an actual
  implementation requirement; never silently drop required failure checks.
- Apply executable strict options for the declared profile. Sourced libraries
  preserve caller options/traps/IFS/cwd/environment unless the API says otherwise.
- Quote argv expansions, check critical statuses, validate operands and keep
  stdout for data. Do not parse ls or split filename command output.
- Use private owned temporary resources and preserve failure status in cleanup.
- Keep secrets out of argv, xtrace and logs; redact full values.
- Run supported static checks and actual minimum/current interpreter tests.
  Report unsupported tools and unverified utility-platform lanes explicitly.
- Use the packaged gate read-only. Its host requirement differs from file targets;
  a gate pass does not prove runtime compatibility.
- Install hooks or change sandbox/permission configuration only for an explicit
  project integration task, after checking current client documentation.
```

This block deliberately has no universal Bash 4.4 preamble. The extension
`.sh` does not identify a Bash floor. Google uses `#!/bin/bash` and
80-column guidance with exceptions; Artagon may choose a PATH shebang and
strict-option policy explicitly. The 100-line advice concerns language choice,
not an automatic migration command.

## Client files and symlinks

Use the consuming client's current documented instruction mechanism. A relative
symlink target is relative to the link's directory: for a link under `.github/`,
a repository-root target is typically `../AGENTS.md`, not `AGENTS.md`.
Inspect existing paths first; do not overwrite files or force-replace links.
Nested clients may have closer instruction files and distinct discovery rules.

Instruction text, runtime command screening and OS isolation have different
evidence boundaries. An instruction block cannot enforce process confinement.

## Sources

Local correction of `docs/shell-skills-research.md` §§1,6.
[Google Shell Style](https://google.github.io/styleguide/shellguide.html),
[POSIX 2017 shell language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html),
[POSIX 2024 shell language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html).
Historical client adoption counts and hook schemas are intentionally not used
as current operational evidence.
