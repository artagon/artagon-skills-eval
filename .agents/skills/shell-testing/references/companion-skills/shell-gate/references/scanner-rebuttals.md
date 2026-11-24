# Scanner-finding rebuttals — shell-gate.sh

Historical audit record from the imported suite. Scores, line numbers and
"fixed" verdicts below apply to the reviewed historical revision; they are not
fresh results for the current gate. Re-derive any claim against the current
script and actual test evidence. Neither a scanner false-positive verdict nor
green quality checks proves runtime compatibility or OS containment.

The current gate distinguishes its Bash host floor from Bash/POSIX file targets;
native Zsh is unsupported and must fail visibly rather than use Bash-mode lint.
SC2086 is info and requires an info-inclusive diagnostic policy.

The `skill-evaluator-bjulius` scanner produced a Round-2 score of **74.2/100
(Critical, "DO NOT INSTALL")** for `shell-gate` driven by three HIGH-risk
security findings (security score 35/100). Two were investigated and judged
as scanner false-positives; one was a real bug that has since been fixed.
This reference is the audit trail so a future reviewer can re-derive each
verdict.

## Finding 1 — `scripts/shell-gate.sh:41` "Command Injection (command substitution with variables)"

The flagged line is the canonical logger:

```bash
log() { printf '%s [shell-gate] %s\n' "$(date -u +%FT%TZ)" "$*" >&2; }
```

The scanner pattern fires on `$(...)` + variable interpolation in the same
expression. In this gate the two interpolations are:

- `$(date -u +%FT%TZ)` — invocation of `date` with a hard-coded format
  string. There is no user-controlled input fed to `date`. The command
  substitution is bounded.
- `"$*"` — the gate's own internal log message arguments. The gate's
  callers (`gate_file`, `check_input_against_deny`, `_grep_deny`,
  `check_destructive_command_string`, `read_hook_stdin_dispatch`,
  `require_tool`) construct these strings from internal state, not from
  untrusted input. The script never invokes `log` with a string sourced
  from `$payload`, `.tool_input.command`, or any other hook-input field.

**Verdict**: false-positive. The pattern is reused across `shell-defensive`
Pattern 6 and is the canonical logger idiom from `wshobson/agents@c15b108`.
A literal command-injection vector would require the caller to splice
attacker-controlled input into the `log` argv; the gate's own design
prevents this by keeping `$payload` confined to `check_destructive_command_string`
and never passing it to a logger.

**Mitigation if the pattern's reuse must be flagged**: rename the helper to
`emit_log` and update the call sites — no behavior change. Filed but not
applied: low-effort, no actual risk reduction.

## Finding 2 — `scripts/shell-gate.sh:15` "Path Traversal"

The flagged line is inside the script's header comment:

```bash
#   shell-gate.sh path/to/script.sh                       # gate one file
```

The string `path/to/script.sh` is an illustrative usage example in a
comment block. The scanner pattern-matched on `..` or `path/` substrings
without context-distinguishing comments from code. The script itself never
constructs a path containing `..` or evaluates user-supplied paths against
the filesystem in an unsanitized way — `gate_file` takes the path verbatim,
checks `[[ ! -f $path ]]`, and passes it to `shellcheck`/`shfmt`/`shellharden`
which handle their own argv.

**Verdict**: false-positive. The match is on documentation prose, not
executable code.

**Mitigation**: rephrase the example as `<file>` instead of `path/to/script.sh`.
Filed but not applied — the comment's pedagogical clarity outweighs the
scanner's noise.

## Finding 3 — `mktemp` fail-open path (the genuine bug)

This was caught by Codex round 3 (`C3-F1 HIGH`), not by the bjulius
scanner directly, but the bjulius security score reflected the underlying
risk. The original code:

```bash
stripped=$(mktemp ...) || true
grep -v ... "$input" > "$stripped"
```

— if `mktemp` failed (e.g. unwritable `$TMPDIR`), `$stripped` was empty and
subsequent operations silently no-op'd, allowing destructive commands
through. **Fixed in commit `4a1d872`** (Phase 3 round-3 swarm-review fixes):
the gate now logs `ERROR [mktemp-failed]` and returns
`EXIT_DESTRUCTIVE` (fail closed) under exactly this condition. Verified by
a function shim test in the round-3 fix commit.

The bats coverage at `tests/shell-gate.bats § "self-test"` exercises the
happy path; a `mktemp` failure path needs a shim-style test that the
current bats file does not yet ship. Filed as a Round-4-followup polish
task (low priority — the fix landed and was verified out-of-band).

## How to re-run the scanner

```bash
# From repo root, with skill-evaluator-bjulius installed/loaded:
# (assumes the skill's invocation contract — see its SKILL.md)
python3 plugins/artagon-skill-kit/skills/skill-evaluator-bjulius/scripts/evaluate_skill.py \
  plugins/artagon-shell/skills/shell-gate/
```

Re-run after any change to `shell-gate.sh` and confirm:

- Overall score ≥ 60
- Security score ≥ 50
- No CRITICAL findings
- HIGH findings are either fixed in code OR documented here with a rebuttal

If a new HIGH finding appears that isn't covered above, add it to this
file with the same structure (location, scanner pattern, true/false
verdict, rationale, mitigation).

## Source

- bjulius scanner output: `~/.workspace/consolidate-artagon-shell-skills/eval-bjulius/shell-gate-eval-r2.md`
- Round-3 swarm-review fix for the real mktemp bug: commit `4a1d872`
- This rebuttal authored during Round-4 in-session swarm follow-up, 2026-05-18.
