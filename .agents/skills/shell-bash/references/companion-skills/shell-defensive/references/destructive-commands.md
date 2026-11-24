# Destructive-command gating

This reference concerns explicitly authorized destructive workflows, not
permission to execute its examples. Declare interpreter, source/execute role
and utility dependencies. Empty variables, final symlinks, unexpected roots,
option-like paths and races need separate controls. Command-string screening
is advisory; it cannot confine filesystem access.

## The `:?` guard — cheapest possible gate

The `${VAR:?error message}` parameter expansion exits the shell if `VAR` is unset
*or* empty, printing the message to stderr. Use it inline on every destructive
command that references a variable:

```bash
rm -rf -- "${BUILD_DIR:?BUILD_DIR must be set}"/*
git -C "${REPO:?REPO must be set}" clean -fdx
```

If `BUILD_DIR` is empty or unset, the shell exits *before* invoking `rm`. No
log file required. No conditional required. The `:?` form is preferred over
`:-`/`:=` (which substitute defaults) and over `${VAR?...}` (which only catches
unset, not empty).

## The `--` separator

Always insert `--` between the command and its path arguments. Without it, a
filename that begins with a hyphen is parsed as a flag:

```bash
# DANGEROUS: a file named "-rf" plus another arg ends very badly
rm "$file" "$dir"

# SAFE: -- ends option parsing
rm -- "$file" "$dir"
git checkout -- "$file"
```

Use the command's documented option/operand boundary; `--` support and grammar
are utility-specific. In portable utilities without that form, an explicit
`./` pathname may prevent a leading dash from becoming an option.

## `safe_rm` — refuses the catastrophic cases

```bash
safe_rm() {
  [[ $# -eq 1 ]] || return 1
  local target="$1"
  [[ -z "$target" || "$target" == "/" || -L "$target" ]] && {
    echo "refusing rm '$target'" >&2
    return 1
  }
  local real
  local home_real
  real=$(realpath -- "$target") || return 1
  home_real=$(realpath -- "${HOME:?HOME must be set}") || return 1
  [[ "$real" == "/" || "$real" == "$home_real" ]] && {
    echo "refusing rm '$real'" >&2
    return 1
  }
  rm -rf -- "$real"
}
```

This existing Bash helper API requires a compatible `realpath --` utility.
It rejects a final symlink and compares canonical home/root paths, but it is
only an example refusal list, not a complete safety boundary. Parent symlinks,
trailing slashes, protected ancestors, target substitution and TOCTOU races
still require a trusted owned tree and explicit authorized-root policy.

Never replace realpath with parent `cd -P` plus basename: that leaves the
final-file symlink unresolved. POSIX 2017 does not require a realpath command;
POSIX 2024 does not standardize every GNU option. If a required resolver is
absent or incompatible, fail closed instead of pretending to canonicalize.

Add `/boot`, `/etc`, `/usr`, `/var/lib`, and any production data root to the
refusal list when shipping into multi-tenant or production hosts.

## Git push: `--force-with-lease`, never `--force`

`git push --force` will clobber upstream work that landed since the last
fetch. `git push --force-with-lease=ref:expected_sha` refuses to push if
upstream has moved. The cost of being wrong with `--force` is a colleague's
work erased silently.

```bash
# Wrong
git push --force origin main

# Right
git push --force-with-lease=refs/heads/main:"$EXPECTED_SHA" origin "$BRANCH":refs/heads/main
```

Wire this into the Bash deny-list of the agent runtime (Claude
`permissions.deny`, Codex `[[rules.requirements]]`, Gemini `tools.exclude`).
The `shell-gate` skill ships the per-CLI templates.

## Workstation niceties: `gio trash` over `rm`

On a desktop, `gio trash` (Linux) or `trash` (macOS, via `brew install trash`)
moves files to the OS trash bin instead of unlinking. Recoverable. Use it
wherever interactive cleanup is acceptable; reserve `rm` for non-interactive
batch jobs where trash bins are not appropriate.

## Agent-runtime deny-list bypasses (CVE-2025-66032)

The application-layer deny-lists in Claude / Codex / Gemini hooks are
*bypassable* through shell tricks. CVE-2025-66032 documents eight, including:

- a sed program's `e` command (distinct from sed's `-e` option)
- bash variable construction (`a=rm; "$a" -rf …`)
- configured aliases or wrappers that hide the eventual command
- `node -e "require('child_process').exec('rm -rf …')"`
- `python3 -c "import os; os.system('rm -rf …')"`
- base64-decoded command substitution
- `eval` via aliases

The implication: deny-lists are **defense in depth**, not the actual security
boundary. Pair them with OS sandboxing (Seatbelt on macOS, bwrap+seccomp on
Linux, Docker for cross-platform) — see
`../../shell-gate/references/sandbox-ralph.md`.

## Hard-deny / soft-block / warn-and-fix taxonomy

Adapted from `docs/shell-skills-research.md` § 6 lines 426-432:

- **Hard-deny (always block)**: `rm -rf /`, `rm -rf $HOME`, `rm -rf "$VAR"` with empty `VAR`, `dd of=/dev/sd*`, `mkfs.*`, `git push --force` (without `-with-lease`), `chmod -R 777`, anything piping to `bash`/`sh` from `curl`/`wget`, writes to `/etc`, `/usr`, `/var/lib`, `/boot` outside a container.
- **Soft-block (require human approval)**: `git push` (any), `git reset --hard`, `git checkout -- …`, `find … -delete`, `kubectl delete`, `terraform destroy`, `*DROP TABLE*`/`*TRUNCATE*`, `chmod 777`.
- **Warn-and-fix**: ShellCheck warning-severity findings; shfmt diff; shellharden quoting fixes.

The `shell-gate` skill ships a **representative subset** of this taxonomy as runnable `scripts/shell-gate.sh` logic — specifically the hard-deny `rm` variants (with flag-order swaps, `--` separator, `$HOME` references), `dd of=/dev/<blockdev>`, `mkfs.*`, `chmod -R 777`, `git push --force` (without `-with-lease`), and `curl|sh` pipes. Soft-block patterns (`git reset --hard`, `kubectl delete`, `terraform destroy`, etc.) and system-dir writes (`/etc`, `/usr`, `/var/lib`, `/boot`) are **deliberately NOT in the gate script** — soft-block belongs in the per-CLI permission-rule layer (Claude `permissions.ask`, Codex `[rules.requirements]`, Gemini `tools.exclude`) so the human-in-the-loop sees the prompt, and system-dir writes are deferred to the sandbox layer (see `shell-gate/references/sandbox-ralph.md`). The gate is a soft pattern-grep advisory; **sandbox is the authoritative deny boundary** (CVE-2025-66032 documents 8 deny-list bypass classes).

## Sources

- Patterns synthesized from `docs/shell-skills-research.md` § 2 (lines 79–91)
  + § 6 (lines 426–432) + § closing observations.
- CVE-2025-66032 bypass taxonomy: same research doc, § 4 line 234.
- Existing `safe_rm` example and historical research attribution retained;
  locally corrected on 2026-11-06, not reproduced verbatim.
