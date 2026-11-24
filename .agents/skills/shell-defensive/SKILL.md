---
name: shell-defensive
description: >-
  Hardens shell scripts for unattended jobs and risky file operations with explicit failure, cleanup, signal, and state contracts. Use for production failure paths; not for dialect selection alone.
license: MIT
compatibility: "Requires the declared target interpreter and named utility implementations. Bash examples require their stated version. No MCP server or network access is required for local hardening."
allowed-tools: Read Write Edit Glob Grep Bash
metadata:
  version: "1.2.0"
  status: experimental
  upstream: "wshobson/agents@c15b108 (MIT), locally corrected and extended"
---

# Defensive shell coding

Skill marker: `artagon-shell/shell-defensive/v1`.

## Establish the boundary

Read the [target contract](references/target-contract.md) before using a recipe.
Declare Bash 3.2 or a newer feature floor, POSIX 2017/2024 or native Zsh,
source/execute mode and actual GNU/BSD/BusyBox dependencies. A language selector
answers dialect questions; this workflow owns failure and state behavior.

## Production patterns

The [Bash catalog](references/defensive-patterns.md) gives versioned examples:

1. Use compatible strict options for executables and explicit status checks for
   critical work. Preserve an existing fail-closed policy.
2. Capture the incoming status first in cleanup, retain it if cleanup also fails,
   and translate INT/TERM deliberately. ERR and EXIT have different purposes.
3. Distinguish the physical parent directory from resolution of the final
   symlink. Declare a realpath/readlink dependency when final-target identity
   matters; do not claim parent `pwd -P` resolves it.
4. Create private temporary resources with `mktemp`, check creation and register
   cleanup only for owned resources. Do not reuse the inherited `TMPDIR` variable
   as a scratch path.
5. Validate argument counts before consuming option values; reject unknown flags.
6. Write redacted diagnostics to stderr and keep stdout machine-readable.
7. Make retries idempotent and locks ownership-aware; test interrupted work.
8. Stage atomic writes on the destination filesystem and preserve required
   permissions and metadata. A rename alone is not a durability guarantee.
9. Preserve filename argument boundaries and define empty-list behavior.
   POSIX 2017 can use `find -exec ... {} +`; NUL readers and utility flags need
   declared support.
10. Check every required interpreter and utility feature. A successful
    `command -v` establishes presence, not version or compatible behavior.

## Errexit-safe handling

Keep `-e` as an applicable guardrail, with its exception contexts explicit.
`mycall()` is a definition fragment, not an invocation. `mycall; rc=$?` can
exit before `rc` is assigned. For a simple external command:

```bash
if command_name "$input"; then
  printf '%s\n' 'completed'
else
  rc=$?
  printf 'command_name failed (%s)\n' "$rc" >&2
  exit "$rc"
fi
```

A function called in `if`, `while`, negation or an AND/OR list cannot rely on
errexit internally. It must check each critical step, for example
`copy_input "$1" || return "$?"`. `inherit_errexit` exists from Bash 4.4 and
does not remove conditional-context exceptions. Sourced libraries must not
silently alter callers' options, traps, IFS, cwd or environment.

## Risk-specific references

- [Destructive commands](references/destructive-commands.md): guards and exact targets; string screening is advisory.
- [Cross-platform operations](references/cross-platform.md): shell syntax and utility dependencies are separate.
- [Idempotency and locking](references/idempotency-and-locking.md): retries, state and lock ownership.
- [Secrets](references/secrets-handling.md): avoid argv/xtrace/log leakage; redact complete values.

`"${VAR:?must be set}"` prevents empty input but does not validate the target,
symlink races or authorization. Canonicalization helpers are not sandboxes.
Do not execute destructive review examples.

## Related workflows and sources

- [Authoring](references/companion-skills/shell-authoring/guide.md): style and preserved APIs.
- [Testing](references/companion-skills/shell-testing/guide.md): failure and caller-state assertions.
- [Linting](references/companion-skills/shell-linting/guide.md): reviewed static diagnostics.
- [Gate](references/companion-skills/shell-gate/guide.md): packaged read-only checks.

Catalog lineage: `wshobson/agents@c15b108`, MIT. Additional hardening questions
were informed by the inspected pvillega and rikdc sources; their code was not
copied and blanket removal of errexit was rejected. Version/standards sources
and pinned portability sources appear in the target contract.

## Harmless invocation

`shell-defensive review cleanup and status propagation without running the job`.
Return findings and an inert test plan; report `mutations=none`.

## Output contract

Report the target contract, failure scenario, exact changed files/findings,
executed checks, unsupported environments and residual risks. Distinguish static
review, available-tool identity and executed behavior.
