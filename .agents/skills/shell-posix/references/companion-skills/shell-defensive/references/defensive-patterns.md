# Defensive bash patterns — full code catalog

This catalog was absorbed from `wshobson/agents@c15b108`, MIT, during the
2026-05-17 consolidation and corrected locally on 2026-11-06. It is active
guidance, not a verbatim upstream snapshot. Existing example function APIs are
retained. Examples are Bash executables unless marked otherwise; declare the
minimum version and utility implementations before use. They are not sourced
library preambles or native-Zsh recipes.

## Table of contents

- [Pattern 1: Strict-mode preamble](#pattern-1-strict-mode-preamble)
- [Pattern 2: ERR + EXIT traps](#pattern-2-err--exit-traps)
- [Pattern 3: Safe script-dir detection](#pattern-3-safe-script-dir-detection)
- [Pattern 4: Safe tempdir hygiene](#pattern-4-safe-tempdir-hygiene)
- [Pattern 5: Robust argument parsing](#pattern-5-robust-argument-parsing)
- [Pattern 6: Structured logging](#pattern-6-structured-logging)
- [Pattern 7: Idempotent state checks](#pattern-7-idempotent-state-checks)
- [Pattern 8: Safe file operations](#pattern-8-safe-file-operations)
- [Pattern 9: NUL-safe iteration](#pattern-9-nul-safe-iteration)
- [Pattern 10: Dependency checks](#pattern-10-dependency-checks)
- [Advanced: named parameters](#advanced-named-parameters)
- [Advanced: process orchestration with signals](#advanced-process-orchestration-with-signals)
- [Advanced: variable safety + array handling](#advanced-variable-safety--array-handling)
- [Advanced: conditional safety](#advanced-conditional-safety)
- [Advanced: comprehensive function template](#advanced-comprehensive-function-template)
- [Best-practices summary](#best-practices-summary)

## Pattern 1: Strict-mode preamble

For an executed Bash 4.4+ profile whose contract enables these guardrails:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail  # Exit on error, unset variables, pipe failures
shopt -s inherit_errexit  # Bash >= 4.4 only
```

**Flag breakdown:**

- `set -E` — inherit ERR trap into functions and command substitutions
- `set -e` — exit on unhandled failures outside its documented exceptions
- `set -u` — exit on undefined variable reference
- `set -o pipefail` — pipe fails if ANY command in it fails, not just the last
Do not apply this preamble to Bash 3.2, POSIX sh or native Zsh. Bash 3.2 has
no inherit_errexit; propagate critical statuses explicitly. A global IFS change
is a separate policy choice and does not replace quoting. Sourced libraries
must preserve the caller's declared state. Conditional functions must check
internal failures explicitly; `cmd; rc=$?` can exit before assignment under -e.

## Pattern 2: ERR + EXIT traps

Capture `$?` as the first thing the cleanup function does, then exit with that
code so the real failure status survives.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

scratch_dir=
cleanup() {
    local rc=$?
    local cleanup_rc=0
    trap - EXIT
    if [[ -n "$scratch_dir" ]]; then
        rm -rf -- "$scratch_dir" || cleanup_rc=$?
    fi
    if (( rc == 0 && cleanup_rc != 0 )); then
        rc=$cleanup_rc
    fi
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'printf "Error on line %s\n" "$LINENO" >&2' ERR

scratch_dir=$(mktemp -d) || exit "$?"
# Script code here
```

**Why this matters:** if cleanup does *anything* before `local rc=$?`, the last
command's exit code overwrites the real failure. SIGKILL cannot be trapped —
depend on external sweepers (systemd, tmpreaper) for kill-9 cases.

Single-quote the trap command at registration so `$scratch_dir` expands at *firing*
time, not registration time:

```bash
trap 'rm -rf -- "$scratch_dir"' EXIT   # single quotes — expands on EXIT
trap "rm -rf -- '$scratch_dir'" EXIT   # double quotes — expands NOW (bad)
```

## Pattern 3: Safe script-dir detection

Determines the physical parent of a Bash source path while preserving spaces.
It does not resolve a final-file symlink.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Correctly determine script directory
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SCRIPT_NAME="$(basename -- "${BASH_SOURCE[0]}")"

echo "Script location: $SCRIPT_DIR/$SCRIPT_NAME"
```

`BASH_SOURCE[0]` identifies the current Bash source file, including when sourced.
`cd --` defends against directories that begin with a hyphen. `pwd -P` resolves
parent-directory symlinks; use `pwd` to preserve the logical parent path. For a
final symlink target, require a compatible resolver and fail closed if absent.
Do not use the executable preamble when copying this into a sourced library.

## Pattern 4: Safe tempdir hygiene

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Create temporary directory
scratch_dir=$(mktemp -d) || { echo "ERROR: Failed to create temp directory" >&2; exit 1; }
trap 'rm -rf -- "$scratch_dir"' EXIT

# Create temporary files in directory
tmpfile1="$scratch_dir/temp1.txt"
tmpfile2="$scratch_dir/temp2.txt"

# Use temporary files
touch "$tmpfile1" "$tmpfile2"

printf 'Temp files created in: %s\n' "$scratch_dir"
```

**Don't** use `/tmp/myscript-$$` — PID reuse + predictability make it a TOCTOU
vector. `mktemp -d` returns a private dir with 700 perms.

The short trap illustrates ownership and registration order. Use Pattern 2 when
cleanup errors must affect the result without hiding the original failure.
Do not overwrite the inherited TMPDIR environment variable. For secrets, verify
the storage's actual privacy and persistence properties; no shred guarantee.

## Pattern 5: Robust argument parsing

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Default values
VERBOSE=false
DRY_RUN=false
OUTPUT_FILE=""
THREADS=4

usage() {
    cat <<EOF >&2
Usage: $0 [OPTIONS]

Options:
    -v, --verbose       Enable verbose output
    -d, --dry-run       Run without making changes
    -o, --output FILE   Output file path
    -j, --jobs NUM      Number of parallel jobs
    -h, --help          Show this help message
EOF
    # Default exit 1: misuse path. Explicit `usage 0` for the --help branch.
    # Default-0 here would cause CI to treat a misused script (no args /
    # unknown flag) as a successful no-op (a "ghost pass").
    exit "${1:-1}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -o|--output)
            [[ $# -ge 2 ]] || usage 1
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -j|--jobs)
            [[ $# -ge 2 ]] || usage 1
            THREADS="$2"
            shift 2
            ;;
        -h|--help)
            usage 0
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "ERROR: Unknown option: $1" >&2
            usage 1
            ;;
    esac
done

# Validate required arguments
[[ -n "$OUTPUT_FILE" ]] || { echo "ERROR: -o/--output is required" >&2; usage 1; }
```

The explicit `--` arm lets users pass paths that begin with a hyphen.
`usage "${1:-1}"` accepts an exit-code argument so callers can distinguish
help-from-`-h` (caller passes `0`) vs help-from-misuse (no arg → default `1`).
The default exit `1` matters in CI: if `usage` is called bare on an error
path, the script must NOT silently exit `0` and let the CI step claim
success — that's the "ghost pass" risk.

## Pattern 6: Structured logging

Everything to stderr (so stdout stays parseable as data). ISO-8601 timestamps.
DEBUG gated on environment variable.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Logging functions
log_info() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $*" >&2
}

log_warn() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] WARN: $*" >&2
}

log_error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2
}

log_debug() {
    if [[ "${DEBUG:-0}" == "1" ]]; then
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] DEBUG: $*" >&2
    fi
}

# Usage
log_info "Starting script"
log_debug "Debug information"
log_warn "Warning message"
log_error "Error occurred"
```

For secret redaction in logs, see
`secrets-handling.md § "Redaction in logs"`.

## Pattern 7: Idempotent state checks

Re-running must be cheap and harmless.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Check if resource already exists
ensure_directory() {
    local -r dir="$1"

    if [[ -d "$dir" ]]; then
        log_info "Directory already exists: $dir"
        return 0
    fi

    mkdir -p "$dir" || {
        log_error "Failed to create directory: $dir"
        return 1
    }

    log_info "Created directory: $dir"
}

# Ensure configuration state
ensure_config() {
    local -r config_file="$1"
    local -r default_value="$2"

    if [[ ! -f "$config_file" ]]; then
        echo "$default_value" > "$config_file"
        log_info "Created config: $config_file"
    fi
}

# Rerunning script multiple times should be safe
ensure_directory "/var/cache/myapp"
ensure_config "/etc/myapp/config" "DEBUG=false"
```

For single-instance enforcement (only one copy of the script running),
see `idempotency-and-locking.md § "Pattern 3: flock for single-instance enforcement"`.

## Pattern 8: Safe file operations

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Use -i flag to move safely without overwriting
safe_move() {
    local -r source="$1"
    local -r dest="$2"

    if [[ ! -e "$source" ]]; then
        echo "ERROR: Source does not exist: $source" >&2
        return 1
    fi

    if [[ -e "$dest" ]]; then
        echo "ERROR: Destination already exists: $dest" >&2
        return 1
    fi

    mv -- "$source" "$dest"
}

# Safe directory cleanup
safe_rmdir() {
    local -r dir="$1"

    if [[ ! -d "$dir" ]]; then
        echo "ERROR: Not a directory: $dir" >&2
        return 1
    fi

    # Use -I flag to prompt before rm (BSD/GNU compatible)
    rm -rI -- "$dir"
}

# Atomic file writes
atomic_write() {
    local -r target="$1"
    local tmpfile
    local rc
    tmpfile=$(mktemp "${target}.XXXXXX") || return "$?"

    # Write to temp file first
    if cat > "$tmpfile"; then
        :
    else
        rc=$?
        rm -f -- "$tmpfile" || :
        return "$rc"
    fi

    # Atomic rename requires staging on the destination filesystem.
    if mv -- "$tmpfile" "$target"; then
        return 0
    else
        rc=$?
        rm -f -- "$tmpfile" || :
        return "$rc"
    fi
}
```

This helper checks its own input-copy status. Do not feed a fallible producer
through a pipeline and assume a later pipefail status prevents publication:
the consumer can already have renamed partial data. Stage and validate producer
output first. Review destination type, permissions and durability separately.

For the full destructive-command gating layer (refusing `rm /`,
`rm $HOME`, etc.), see
`destructive-commands.md`.

## Pattern 9: NUL-safe iteration

The canonical "don't parse `ls`, don't iterate `$(find …)`" pattern.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Use $() instead of backticks
name=$(<"$file")  # Modern, safe variable assignment from file
output=$(command -v python3)  # Get command location safely

# Handle command substitution with error checking
result=$(command -v node) || {
    log_error "node command not found"
    return 1
}

# For multiple lines into an array
mapfile -t lines < <(grep "pattern" "$file")

# NUL-safe iteration over find output
while IFS= read -r -d '' file; do
    echo "Processing: $file"
done < <(find /path -type f -print0)
```

`-print0` + Bash `read -r -d ''` preserves filename boundaries where the
utility supports it. It is not the only correct form: `find -exec ... {} +`
is a POSIX-2017 alternative and runs nothing on an empty set. Check the
producer's status separately; process substitution does not propagate it.
`mapfile`/`readarray` require Bash 4.0+, and `mapfile -d` needs 4.4+.

## Pattern 10: Dependency checks

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

check_dependencies() {
    local -a missing_deps=()
    local -a required=("jq" "curl" "git")

    for cmd in "${required[@]}"; do
        if ! command -v "$cmd" &>/dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo "ERROR: Missing required commands: ${missing_deps[*]}" >&2
        return 1
    fi
}

check_dependencies
```

`command -v` is the POSIX way. `which` is non-POSIX and inconsistent across
distros; `type` works but is more verbose. Run dependency checks at startup
(before doing any work), not lazily, so failures are loud and early.

## Advanced: named parameters

Function-level `--input=`, `--output=` parsing for internal APIs.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

process_data() {
    local input_file=""
    local output_dir=""
    local format="json"

    # Parse named parameters
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --input=*)
                input_file="${1#*=}"
                ;;
            --output=*)
                output_dir="${1#*=}"
                ;;
            --format=*)
                format="${1#*=}"
                ;;
            *)
                echo "ERROR: Unknown parameter: $1" >&2
                return 1
                ;;
        esac
        shift
    done

    # Validate required parameters
    [[ -n "$input_file" ]] || { echo "ERROR: --input is required" >&2; return 1; }
    [[ -n "$output_dir" ]] || { echo "ERROR: --output is required" >&2; return 1; }
}
```

## Advanced: process orchestration with signals

Track background PIDs and propagate SIGTERM/SIGINT.

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Track background processes
PIDS=()

cleanup() {
    log_info "Shutting down..."

    # Terminate all background processes
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done

    # Wait for graceful shutdown
    for pid in "${PIDS[@]}"; do
        wait "$pid" 2>/dev/null || true
    done
}

trap cleanup SIGTERM SIGINT

# Start background tasks
background_task &
PIDS+=("$!")

another_task &
PIDS+=("$!")

# Wait for all background processes
wait
```

For larger fan-out, use `xargs -0 -P8 -n1` with `find -print0` or GNU parallel.
For durable background jobs, use `tmux new-session -d -s name 'cmd'` or
systemd-run, not `nohup &; disown`.

## Advanced: variable safety + array handling

```bash
# Wrong - unsafe
cp $source $dest

# Correct - safe
cp -- "$source" "$dest"

# Required variables - fail with message if unset
: "${REQUIRED_VAR:?REQUIRED_VAR is not set}"

# Safe array iteration
declare -a items=("item 1" "item 2" "item 3")

for item in "${items[@]}"; do
    echo "Processing: $item"
done

# Reading output into array safely
mapfile -t lines < <(some_command)
readarray -t numbers < <(seq 1 10)
```

The `${VAR:?…}` form is the cheapest possible destructive-command gate — see
`destructive-commands.md § "The :? guard — cheapest possible gate"`.

## Advanced: conditional safety

```bash
# Bash - safer (no word-splitting on RHS)
if [[ -f "$file" && -r "$file" ]]; then
    content=$(<"$file")
fi

# POSIX - portable
if [ -f "$file" ] && [ -r "$file" ]; then
    content=$(cat "$file")
fi

# Test for existence before operations
if [[ -z "${VAR:-}" ]]; then
    echo "VAR is not set or is empty"
fi
```

`[[ ]]` is a bash keyword (not a command) — no word-splitting on the RHS, no
glob expansion, supports `=~` regex matching. Always prefer it in bash scripts.
Use `[ ]` only when the script must run under strict POSIX `sh`.

## Advanced: comprehensive function template

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

# Prefix for functions: handle_*, process_*, check_*, validate_*
# Include documentation and error handling

validate_file() {
    local -r file="$1"
    local -r message="${2:-File not found: $file}"

    if [[ ! -f "$file" ]]; then
        echo "ERROR: $message" >&2
        return 1
    fi
    return 0
}

process_files() {
    local -r input_dir="$1"
    local -r output_dir="$2"

    # Validate inputs
    [[ -d "$input_dir" ]] || { echo "ERROR: input_dir not a directory" >&2; return 1; }

    # Create output directory if needed
    mkdir -p "$output_dir" || { echo "ERROR: Cannot create output_dir" >&2; return 1; }

    # Process files safely
    while IFS= read -r -d '' file; do
        echo "Processing: $file"
        # Do work
    done < <(find "$input_dir" -maxdepth 1 -type f -print0)

    return 0
}
```

## Advanced: dry-run support

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

DRY_RUN="${DRY_RUN:-false}"

run_cmd() {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "[DRY RUN] Would execute: $*" >&2
        return 0
    fi

    "$@"
}

# Usage
run_cmd cp -- "$source" "$dest"
run_cmd rm -- "$file"
run_cmd chown "$owner" "$target"
```

Dry-run logs go to stderr so stdout stays parseable. The `run_cmd` wrapper is
trivial to add and pays for itself the first time a path argument is wrong.

## Best-practices summary

1. **Use the declared executable failure policy** — version-gate Bash features and explicitly propagate critical statuses; preserve caller state for libraries.
2. **Quote all variables** — `"$variable"` prevents word splitting
3. **Use `[[ ]]` conditionals** — More robust than `[ ]`
4. **Implement error trapping** — Catch and handle errors with `$?` capture
5. **Validate all inputs** — Check file existence, permissions, formats
6. **Use functions for reusability** — Prefix with meaningful names
7. **Implement structured logging** — Include timestamps and levels, all to stderr
8. **Support dry-run mode** — Allow users to preview changes
9. **Handle temporary files safely** — Use `mktemp -d`, cleanup with trap
10. **Design for idempotency** — Scripts should be safe to rerun
11. **Document requirements** — List dependencies and minimum versions
12. **Test error paths** — Ensure error handling works correctly
13. **Use `command -v`** — Safer than `which` for checking executables
14. **Prefer `printf` over `echo`** — More predictable across systems

## Source

- Original content from `wshobson/agents@c15b108`, MIT licensed.
- Absorbed into `shell-defensive` during Phase 4 consolidation, 2026-05-17.
- See `plugins/artagon-shell/UPSTREAM-wshobson-shell-scripting.md` for the
  full upstream attribution.
