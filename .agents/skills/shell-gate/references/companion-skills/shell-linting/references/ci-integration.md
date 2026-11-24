# CI integration for declared shell targets

Keep CI checks read-only unless a task explicitly authorizes fixes. Inspect the
repository's current configuration, file inventory and dependency pins first.
The 2026-11-06 research inspected ShellCheck 0.11.0, shfmt 3.14.1 and
Shellharden 4.3.2; those observations do not prove the CI runner has them.

## Filename-safe discovery

Do not expand `$(git ls-files ...)` into arguments or use Make's whitespace
lists for filenames. Spaces, newlines, globs and leading dashes must survive.
This Bash 3.2+ example checks an explicitly **Bash-only** tracked directory;
the directory is a project-specific example, not a rule that every .sh is Bash:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

list_file=$(mktemp) || exit 1
trap 'rm -f -- "$list_file"' EXIT
# Production inventories must also name extensionless files and sourced libraries.
git ls-files -z -- 'scripts/bash/' > "$list_file" || exit "$?"

while IFS= read -r -d '' script_file; do
  shfmt -ln bash -d -i 2 -ci -bn -- "$script_file" || exit "$?"
  shellharden --check -- "$script_file" || exit "$?"
  shellcheck --shell=bash --format=json1 --severity=info -x -- "$script_file" || exit "$?"
done < "$list_file"
```

An empty list invokes no analyzers. Discovery failure exits nonzero instead of
looking like an empty clean inventory. This form does not assume GNU xargs
`-r` or POSIX-2024 `-0/-r` on an older utility target.

For a mixed tree, keep dialects in the inventory and dispatch explicitly:
POSIX sh gets `shfmt -ln posix` and ShellCheck's declared sh/dash profile;
Shellharden is Bash-only. Native Zsh gets native syntax review and only supported
formatter constructs, with unsupported coverage visible. The packaged gate
currently fails native-Zsh targets rather than certifying them.

## Shared runner, thin integrations

Use one reviewed project runner from pre-commit, lefthook, GitHub Actions,
GitLab CI, Make or a local hook. Pass filenames as argv or use its NUL manifest
interface. Verify the integration's quoting semantics with hostile filenames;
a `{staged_files}` string is not automatically an argv-safe contract.

A thin Make target can call the runner without interpolating a file list:

```makefile
.PHONY: lint-shell
lint-shell:
	./scripts/lint_shell.sh
```

A pre-commit integration can pass filenames to a runner that declares each
target profile:

```yaml
repos:
  - repo: local
    hooks:
      - id: shell-quality
        name: shell quality
        entry: scripts/lint_shell.sh
        language: system
        types: [shell]
```

These paths are examples to implement for the consuming project, not shipped
files. Include tracked extensionless and native-Zsh files in trigger filters;
`**/*.sh` alone is incomplete. The `types: [shell]` filter and filename rules
must be verified against the project's inventory.

Pin and verify dependencies using the consuming project's established supply
chain process. Do not install tools, hooks or global configuration as a side
effect of a check. Review optional checks and external-source scope.

## Failure and evidence policy

Use `--severity=info` when SC2086 quoting coverage is intended; warning-only
runs omit it. Preserve distinct analyzer findings and tool errors. Shellharden
4.3.2 check status 2 denotes proposed changes. Do not convert every nonzero code
to a pass or swallow discovery failures with `|| true`.

Record actual binary versions, selected language profiles, exit codes and
runtime matrix cells separately. No CI syntax/static pass proves Bash 3.2,
POSIX 2017/2024 or GNU/BSD utility behavior.

## Sources

Local corrections to `docs/shell-skills-research.md` §3 recipes.
[ShellCheck 0.11.0 manual](https://github.com/koalaman/shellcheck/blob/v0.11.0/shellcheck.1.md),
[shfmt 3.14.1](https://github.com/mvdan/sh/blob/v3.14.1/cmd/shfmt/shfmt.1.scd),
[Shellharden 4.3.2](https://github.com/anordal/shellharden/blob/v4.3.2/README.md).
The inspected abdullahkhawer Apache-2.0 source informed configuration-first,
check/diff-first adoption; these examples are local adaptations.
