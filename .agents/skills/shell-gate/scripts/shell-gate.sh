#!/usr/bin/env bash
# shell-gate.sh — static Bash/sh gate and advisory command screening.
#
# Pipeline order: explicit-dialect shfmt, Shellharden for Bash, ShellCheck
# through informational severity. All checks are read-only. A clean result
# does not establish a minimum interpreter version or POSIX edition.
#
# Exit codes:
#   0 — clean
#   1 — findings, unavailable tools, or unsupported dialect
#   2 — destructive (block under agent hook contract)
#
# Usage:
#   shell-gate.sh path/to/script.sh                       # gate one file
#   shell-gate.sh a.sh b.sh                               # gate many
#   shell-gate.sh --shell bash library.sh                 # sourced Bash
#   echo '{"tool_input":{"file_path":"a.sh"}}' | shell-gate.sh --hook-stdin
#     (Claude PostToolUse Edit|Write — file mode)
#   echo '{"tool_input":{"command":"rm -rf /"}}' | shell-gate.sh --hook-stdin
#     (Gemini BeforeTool run_shell_command / Codex PreToolUse Bash — command mode)
#
# Host: Bash 4.4+. Static checks: shellcheck >=0.11.0, shfmt >=3.12.0;
# shellharden >=4.3.1 for Bash targets only. Native Zsh returns unsupported.
# Optional: jq (used only when --hook-stdin is set).
#
# SOFT LAYER. The destructive-command check is a pattern grep, NOT a sandbox.
# It catches common bypass classes (rm flag-swaps, HOME variants, dd to
# block devices, filesystem-create, recursive open-perms, forced git push,
# curl-to-shell pipes) but cannot enumerate every bypass — see CVE-2025-66032
# documenting 8 classes of deny-list evasion (sed e-command, base64
# substitution, eval, etc.).
# Real safety requires sandbox per ../SKILL.md § Sandbox is mandatory.
#
# See ../SKILL.md and references/hook-configs.md for agent-runtime wiring.

readonly EXIT_CLEAN=0
readonly EXIT_FINDINGS=1
readonly EXIT_DESTRUCTIVE=2

if ((BASH_VERSINFO[0] < 4 || (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] < 4))); then
  printf '%s\n' 'shell-gate: host requires Bash 4.4+; target-script compatibility is separate' >&2
  exit "$EXIT_FINDINGS"
fi
set -Eeuo pipefail
shopt -s inherit_errexit

log() { printf '%s [shell-gate] %s\n' "$(date -u +%FT%TZ)" "$*" >&2; }

require_tool() {
  local tool=$1
  command -v -- "$tool" >/dev/null 2>&1 || {
    log "ERROR: required tool not on PATH: $tool"
    exit "$EXIT_FINDINGS"
  }
}

shell_dialect() {
  local path=$1
  local first=''
  IFS= read -r first <"$path" || true
  if [[ $first == '#!'* && $first =~ (^|[[:space:]/])(bash|sh|dash|ash|zsh|ksh|ksh93|mksh|pdksh|lksh|fish|nu)([[:space:]]|$) ]]; then
    case "${BASH_REMATCH[2]}" in
      dash | ash) printf '%s\n' sh ;;
      ksh | ksh93 | mksh | pdksh | lksh) printf '%s\n' ksh ;;
      *) printf '%s\n' "${BASH_REMATCH[2]}" ;;
    esac
    return
  fi
  case "${path##*/}" in
    *.bash | .bashrc | .bash_profile) printf '%s\n' bash ;;
    *.sh) printf '%s\n' sh ;;
    *.zsh | .zshrc | .zshenv | .zprofile | .zlogin | .zlogout) printf '%s\n' zsh ;;
    *.ksh | *.mksh | .kshrc) printf '%s\n' ksh ;;
    *.fish) printf '%s\n' fish ;;
    *.nu) printf '%s\n' nu ;;
    *) printf '%s\n' none ;;
  esac
}

is_shell_file() {
  [[ $(shell_dialect "$1") != none ]]
}

# Run the deny-list pattern checks against an input file (or /dev/stdin).
# Each rule is one grep -qE call so the matched class is loggable.
# Patterns deliberately conservative to avoid noisy false positives; closing
# every bypass is impossible without a real lexer — see header note.
#
# Comment stripping: ONLY whole-line comments (^[[:space:]]*#...) are removed.
# Inline `cmd # comment` is NOT stripped because naive inline-strip is a
# bypass: `printf "x # y"; rm -rf /etc` would lose its destructive tail.
# Whole-line comments are safe to strip (the line has no command).
# Cleanup is via explicit `rm -f -- "$stripped"` at every return path, not a
# RETURN trap — RETURN traps are global and get clobbered by nested function
# calls (e.g., check_destructive_command_string -> check_input_against_deny).
check_input_against_deny() {
  local input=$1
  local context=${2:-$input}
  local stripped rc=0
  if ! stripped=$(mktemp -t shell-gate-stripped.XXXXXX 2>/dev/null); then
    # Fail CLOSED: if we cannot allocate the comment-stripped tempfile, we
    # cannot run the deny check, so we must refuse to approve. Returning
    # EXIT_DESTRUCTIVE here keeps the gate safe even when the calling code
    # suppresses errexit via `|| rc=$?`.
    log "ERROR [mktemp-failed]: cannot allocate stripped tempfile (TMPDIR=${TMPDIR:-/tmp} not writable?); failing closed for $context"
    return "$EXIT_DESTRUCTIVE"
  fi
  # Keep output-open failures separate from grep's status 1 for comment-only input.
  if {
    grep -v -E '^[[:space:]]*#' "$input" || rc=$?
  } >"$stripped" 2>/dev/null; then
    :
  else
    rc=2
  fi
  if ((rc > 1)); then
    log "ERROR [strip-failed]: cannot write stripped copy of $context; failing closed"
    rm -f -- "$stripped"
    return "$EXIT_DESTRUCTIVE"
  fi
  if _grep_deny "$stripped" "$context"; then
    rm -f -- "$stripped"
    return "$EXIT_CLEAN"
  else
    rc=$?
    rm -f -- "$stripped"
    return "$rc"
  fi
}

# A match or an unavailable scan requires denial. Only status 1 proves no match.
_grep_requires_deny() {
  local pattern=$1 input=$2
  local rc=0
  grep -qE "$pattern" "$input" || rc=$?
  if ((rc > 1)); then
    log "ERROR [deny-scan-failed]: cannot inspect input; failing closed"
    return 0
  fi
  return "$rc"
}

# Inner: runs the deny greps against an already-prepared input. Returns
# EXIT_CLEAN on no match, EXIT_DESTRUCTIVE on first match (with log line).
# Factored out so check_input_against_deny owns the tempfile lifecycle.
_grep_deny() {
  local input=$1
  local context=$2

  # rm flag-group fragments (covered: -rf, -fr, -rfv/-Rfv, -r -f / -f -r,
  # --recursive --force in either order). Built once and reused below so the
  # rootpath and HOME rules stay aligned. Round-4 additions: each pattern now
  # ALSO accepts a leading `-- ` (option-terminator) so `rm -- -rf /` —
  # the option-terminator evasion that shell-defensive itself teaches as a
  # defensive idiom — is caught.
  local rm_flags
  rm_flags='([[:space:]]+(--[[:space:]]+)?-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*'
  rm_flags+='|[[:space:]]+(--[[:space:]]+)?-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*'
  rm_flags+='|[[:space:]]+(--[[:space:]]+)?-[rR][[:space:]]+-[fF]'
  rm_flags+='|[[:space:]]+(--[[:space:]]+)?-[fF][[:space:]]+-[rR]'
  rm_flags+='|[[:space:]]+(--[[:space:]]+)?--recursive[[:space:]]+--force'
  rm_flags+='|[[:space:]]+(--[[:space:]]+)?--force[[:space:]]+--recursive)'

  # Optional `--` option-terminator between flags and target.
  local rm_sep='[[:space:]]+(--[[:space:]]+)?'
  local quote='["'"'"']?'

  # rootpath target: /, //, /+sub, with terminator that is whitespace, EOL,
  # close-paren (Round-4: `(rm -rf /)` subshell wrap), quote, or
  # statement-separator. Or `/` followed by a letter so /etc still matches.
  local root_tgt='(/+([[:space:]"'"'"';&|)]|$)|/[a-zA-Z])'

  # HOME target: $HOME or ${HOME}, optionally quoted; terminated by /, ", ',
  # }, whitespace, ;, &, |, ), or EOL. Avoids \b (not honored by BSD grep).
  local home_tgt='\$\{?HOME([/}"'"'"'[:space:];&|)]|$)'

  if _grep_requires_deny "(^|[^[:alnum:]_])rm${rm_flags}${rm_sep}${quote}${root_tgt}" "$input"; then
    log "DESTRUCTIVE [unguarded-rm-rf-rootpath] in $context"
    return "$EXIT_DESTRUCTIVE"
  fi
  if _grep_requires_deny "(^|[^[:alnum:]_])rm${rm_flags}${rm_sep}${quote}${home_tgt}" "$input"; then
    log "DESTRUCTIVE [unguarded-rm-rf-HOME] in $context"
    return "$EXIT_DESTRUCTIVE"
  fi

  # dd to a block device — full-disk overwrite (sda/hda/nvme0/disk0/loop0)
  if _grep_requires_deny '(^|[^[:alnum:]_])dd[[:space:]][^|;&]*[[:space:]]of=/dev/(sd[a-z]|hd[a-z]|nvme[0-9]|disk[0-9]|loop[0-9])' "$input"; then
    log "DESTRUCTIVE [dd-to-block-device] in $context"
    return "$EXIT_DESTRUCTIVE"
  fi

  # mkfs.* — filesystem creation (mkfs, mkfs.ext4, mkfs.xfs, ...)
  if _grep_requires_deny '(^|[^[:alnum:]_])mkfs(\.[a-z0-9]+)?[[:space:]]' "$input"; then
    log "DESTRUCTIVE [mkfs-filesystem-create] in $context"
    return "$EXIT_DESTRUCTIVE"
  fi

  # chmod recursive open-perms (world-writable everything). Round-4: accept
  # combined-letter forms like `-Rf`, `-fR`, etc. — single dash + letter group
  # containing R/r, OR `--recursive`.
  if _grep_requires_deny '(^|[^[:alnum:]_])chmod[[:space:]]+(-[a-zA-Z]*[Rr][a-zA-Z]*|--recursive)[[:space:]]+0?777' "$input"; then
    log "DESTRUCTIVE [chmod-recursive-777] in $context"
    return "$EXIT_DESTRUCTIVE"
  fi

  # git push --force without --force-with-lease/-if-includes.
  if _grep_requires_deny '(^|[^[:alnum:]_])git[[:space:]]+push[[:space:]]([^|;&]*[[:space:]])?(-f([[:space:]]|$)|--force([[:space:]]|$))' "$input"; then
    log "DESTRUCTIVE [git-push-force-no-lease] in $context"
    return "$EXIT_DESTRUCTIVE"
  fi

  # curl piped into a shell — supply-chain risk. Round-4: accept absolute
  # paths to the shell (`| /bin/bash`, `| /usr/local/bin/zsh`) in addition to
  # bare names. Pattern: optional `path/to/` prefix then shell-name.
  if _grep_requires_deny 'curl[[:space:]]+[^|]*\|[[:space:]]*(/[^[:space:]]*/)?(bash|sh|zsh|dash|ksh)([[:space:]]|$)' "$input"; then
    log "DESTRUCTIVE [curl-pipe-sh] in $context"
    return "$EXIT_DESTRUCTIVE"
  fi

  # find -delete or find -exec rm with rootpath target — full-tree wipe.
  # Round-4 additions (Codex-persona bypass set: `find / -delete`,
  # `find / -exec rm -rf {} +`). Pattern matches `find` followed by `/+`
  # then either `-delete` or `-exec rm` anywhere before `;`/`+`/EOL.
  if _grep_requires_deny '(^|[^[:alnum:]_])find[[:space:]]+/+([[:space:]][^|;&]*)?-delete([[:space:]]|$)' "$input"; then
    log "DESTRUCTIVE [find-delete-rootpath] in $context"
    return "$EXIT_DESTRUCTIVE"
  fi
  if _grep_requires_deny '(^|[^[:alnum:]_])find[[:space:]]+/+([[:space:]][^|;&]*)?-exec[[:space:]]+rm([[:space:]]|$)' "$input"; then
    log "DESTRUCTIVE [find-exec-rm-rootpath] in $context"
    return "$EXIT_DESTRUCTIVE"
  fi

  return "$EXIT_CLEAN"
}

check_destructive_command_string() {
  # Args: command string (single hook payload from .tool_input.command).
  # Writes the string to a tempfile, dispatches to check_input_against_deny,
  # then cleans up explicitly (RETURN traps are global and would clobber
  # the outer cleanup if nested). Fails CLOSED on mktemp/write failure
  # so an unwritable TMPDIR cannot bypass the deny check.
  local cmd=$1
  local tmp rc=0
  if ! tmp=$(mktemp -t shell-gate-cmd.XXXXXX 2>/dev/null); then
    log "ERROR [mktemp-failed]: cannot allocate command tempfile (TMPDIR=${TMPDIR:-/tmp} not writable?); failing closed"
    return "$EXIT_DESTRUCTIVE"
  fi
  if ! printf '%s\n' "$cmd" >"$tmp" 2>/dev/null; then
    log "ERROR [write-failed]: cannot write command tempfile; failing closed"
    rm -f -- "$tmp"
    return "$EXIT_DESTRUCTIVE"
  fi
  check_input_against_deny "$tmp" "command:<stdin>" || rc=$?
  rm -f -- "$tmp"
  return "$rc"
}

gate_file() {
  local path=$1
  local dialect=${2:-auto}
  if [[ ! -f $path ]]; then
    log "ERROR: not a regular file: $path"
    return "$EXIT_FINDINGS"
  fi
  if [[ $dialect == auto ]]; then
    dialect=$(shell_dialect "$path")
  fi
  if [[ $dialect == none ]]; then
    log "skip: non-shell file (no shell coverage claimed): $path"
    return "$EXIT_CLEAN"
  fi

  local rc=0
  check_input_against_deny "$path" || rc=$?
  if ((rc == EXIT_DESTRUCTIVE)); then
    return "$EXIT_DESTRUCTIVE"
  fi

  case "$dialect" in
    bash | sh) ;;
    *)
      log "UNSUPPORTED: native $dialect requires its own checks; Bash-mode lint cannot validate $path"
      return "$EXIT_FINDINGS"
      ;;
  esac
  require_tool shfmt
  require_tool shellcheck
  local formatter_dialect=bash
  if [[ $dialect == sh ]]; then formatter_dialect=posix; fi
  log "coverage=static dialect=$dialect minimum-version=unverified file=$path"

  # Pipeline order: shfmt -d -> shellharden --check -> shellcheck.
  # In write mode this order is load-bearing (shellcheck-before-shellharden
  # produces SC2086 noise that shellharden then silences). In check mode the
  # files are not modified, so order only affects which diagnostics surface
  # first — keep it consistent with sibling shell-linting/SKILL.md.
  if ! shfmt -ln "$formatter_dialect" -d -i 2 -ci -bn -- "$path" >&2; then
    log "shfmt findings in $path (dialect=$formatter_dialect); review its diff before writing"
    return "$EXIT_FINDINGS"
  fi

  if [[ $dialect == bash ]]; then
    require_tool shellharden
    if ! shellharden --check -- "$path" >&2; then
      log "shellharden findings in $path; review a proposed diff before applying changes"
      return "$EXIT_FINDINGS"
    fi
  fi

  if ! shellcheck --shell="$dialect" --format=json1 --severity=info -x -- "$path" >&2; then
    log "shellcheck findings in $path; no minimum-version or POSIX-edition conformance is implied"
    return "$EXIT_FINDINGS"
  fi

  return "$EXIT_CLEAN"
}

read_hook_stdin_dispatch() {
  # Read JSON from stdin and dispatch on payload shape:
  #   Claude PostToolUse Edit|Write     -> {"tool_input": {"file_path": "..."}}
  #   Gemini BeforeTool run_shell_command -> {"tool_input": {"command": "..."}}
  #   Codex  PreToolUse  Bash             -> {"tool_input": {"command": "..."}}
  # File payload: run the full gate (deny + lint pipeline).
  # Command payload: deny-check the string only (no file to lint).
  require_tool jq
  local payload file_path cmd
  payload=$(cat)
  file_path=$(printf '%s' "$payload" | jq -r '.tool_input.file_path // .tool_input.path // empty')
  cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')

  if [[ -n $file_path ]]; then
    gate_file "$file_path"
    return $?
  fi
  if [[ -n $cmd ]]; then
    check_destructive_command_string "$cmd"
    return $?
  fi
  log "hook-stdin: no actionable payload (expected .tool_input.file_path or .tool_input.command)"
  return "$EXIT_CLEAN"
}

main() {
  if [[ ${1:-} == "--hook-stdin" ]]; then
    read_hook_stdin_dispatch
    return $?
  fi

  local dialect=auto
  if [[ ${1:-} == --help ]]; then
    printf '%s\n' 'usage: shell-gate.sh [--shell auto|bash|sh|zsh] [--] FILE...' \
      'Static Bash/sh checks only; native Zsh is reported unsupported. No target code executes.'
    return "$EXIT_CLEAN"
  fi
  if [[ ${1:-} == --shell ]]; then
    if (($# < 2)); then
      log 'ERROR: --shell requires auto, bash, sh, or zsh'
      return "$EXIT_FINDINGS"
    fi
    dialect=$2
    case "$dialect" in
      auto | bash | sh | zsh) ;;
      *)
        log "ERROR: unknown dialect: $dialect"
        return "$EXIT_FINDINGS"
        ;;
    esac
    shift 2
  fi
  if [[ ${1:-} == -- ]]; then shift; fi

  if (($# == 0)); then
    log "usage: $0 <file.sh> [...]  |  $0 --hook-stdin"
    return "$EXIT_FINDINGS"
  fi

  local worst=0
  local file
  for file in "$@"; do
    local rc=0
    gate_file "$file" "$dialect" || rc=$?
    if ((rc > worst)); then worst=$rc; fi
  done
  return "$worst"
}

main "$@"
