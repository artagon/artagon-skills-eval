# Historical Gemini hook mutation examples

The following April/May 2026 research record is not a verified-current hook
contract. Do not install or execute these transformations without an explicit
project task, current provider-native documentation and isolated tests.
Cross-client exclusivity claims below are historical, not current facts.

Automatic shell-string rewriting is not generally semantics-preserving.
Naively adding quotes or --, or substituting a Git flag, can change arguments,
redirections and authorization scope. Preserve the exact argv contract and
show proposed changes for review; unsupported parsing must fail closed.
The examples are Bash executable sketches, not POSIX or native-Zsh recipes.
Shellharden is Bash-focused; shfmt's incomplete native-Zsh support does not
make it a universal transformation validator.

The single most underrated capability across the three agent CLIs:
**Gemini's `BeforeTool` hooks can mutate `tool_input` before the model's
command executes**. Neither Claude Code (no mutation by design) nor Codex
(parses but rejects mutation) supports this. For agent-shell-safety work,
this turns the hook from a *guard* (deny + log) into a *corrective filter*
(rewrite + permit).

Documented at `docs/shell-skills-research.md` § 4 lines 273–275 and
§ closing observations lines 436–442:

> *"Gemini hooks can mutate tool inputs via `hookSpecificOutput.tool_input`,
> which neither Claude Code (no mutation by design) nor Codex (parses but
> rejects mutation) supports. For agent-shell-safety work specifically,
> that capability is uniquely powerful — a Gemini BeforeTool hook can
> auto-quote variables, add `--` separators, or rewrite `git push --force`
> to `--force-with-lease` *before* the command executes."*

## Protocol

A Gemini `BeforeTool` hook receives stdin JSON:

```json
{
  "tool_name": "run_shell_command",
  "tool_input": { "command": "git push --force origin main" },
  "session_id": "…",
  "user_prompt": "…"
}
```

The hook can return either `permissionDecision: "deny"` (block) OR
`hookSpecificOutput.tool_input` (mutate):

```json
{
  "hookSpecificOutput": {
    "hookEventName": "BeforeTool",
    "tool_input": { "command": "git push --force-with-lease origin main" }
  }
}
```

The model's command is replaced before execution. From the model's
perspective, the safer variant is what runs. No retry loop, no deny-message
the model has to recover from — the hook silently does the right thing.

## Three useful mutation patterns

### 1. Auto-quote unquoted variables

A hook that runs shellharden's `--transform` on the inbound command:

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

payload=$(cat)
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command')

if printf '%s\n' "$cmd" | shellharden --check -- /dev/stdin >/dev/null 2>&1; then
  # Already safe; pass through
  exit 0
fi

# Rewrite via shellharden
safer=$(printf '%s\n' "$cmd" | shellharden --transform -- /dev/stdin)

jq -n --arg c "$safer" '{
  hookSpecificOutput: {
    hookEventName: "BeforeTool",
    tool_input: {command: $c}
  }
}'
```

### 2. Promote `--force` to `--force-with-lease`

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
payload=$(cat)
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command')

if [[ $cmd =~ git[[:space:]]+push[[:space:]]+--force([[:space:]]|$) ]]; then
  safer=$(printf '%s' "$cmd" | sed -E 's/(git[[:space:]]+push[[:space:]]+)--force([[:space:]]|$)/\1--force-with-lease\2/')
  jq -n --arg c "$safer" '{
    hookSpecificOutput: {
      hookEventName: "BeforeTool",
      tool_input: {command: $c}
    }
  }'
else
  exit 0
fi
```

### 3. Insert `--` before paths in destructive commands

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
payload=$(cat)
cmd=$(printf '%s' "$payload" | jq -r '.tool_input.command')

# Already has --? Pass through.
if [[ $cmd == *' -- '* ]]; then exit 0; fi

# rm/cp/mv that takes a path argument — insert --
if [[ $cmd =~ ^(rm|cp|mv)[[:space:]]+(-[a-zA-Z]+[[:space:]]+)?([^-]) ]]; then
  safer=$(printf '%s' "$cmd" | sed -E 's|^(rm|cp|mv)[[:space:]]+(-[a-zA-Z]+[[:space:]]+)?([^-])|\1 \2-- \3|')
  jq -n --arg c "$safer" '{
    hookSpecificOutput: {
      hookEventName: "BeforeTool",
      tool_input: {command: $c}
    }
  }'
else
  exit 0
fi
```

## Why this matters more than the deny path

A deny hook trains the model to expect failure. The model retries with a
slight variant, hits another deny, retries again, eventually gives up or
loops. Wall-clock cost: 3-5 LLM round-trips per blocked command.

A mutation hook is invisible to the model. The safer command just runs.
The model's perception is "I asked for X; X happened." Wall-clock cost:
~10ms (the hook subprocess) per command.

For high-volume agent loops (Ralph-style autonomy), the mutation pattern
is a 10× efficiency improvement over deny + retry.

## Cautions

- **Audit the mutation**: log every rewrite so a human can review what the
  hook is silently changing. The model has no visibility into mutations —
  if a hook bug rewrites `cat file.txt` to `rm file.txt`, the model will
  faithfully report "I ran cat" while the file is gone.
- **Never mutate destructive intent into safer destructive intent silently**:
  if the model asked to `rm -rf /tmp`, don't rewrite to `rm -rf
  /var/tmp` — deny the destructive intent instead.
- **Mutations should be conservative**: shellharden quote-fixes are safe.
  `--force` → `--force-with-lease` is safe (it's strictly more restrictive).
  Inserting `--` before paths is safe. Changing the command's semantic
  intent is NOT.
- **Test the hook itself**: a Gemini hook bug is invisible to the model
  but catastrophic to the user. Wrap the hook in shellcheck + shellharden
  + bats tests.

## When the same intent is needed on Claude Code or Codex

Neither supports tool_input mutation. The fallbacks:

- **Claude Code**: PreToolUse `permissionDecision: "deny"` with a
  reason that suggests the safer command. The model retries.
- **Codex**: PreToolUse hooks can deny but cannot mutate. Pair with
  `[[rules.requirements]]` org-policy rules that deny the unsafe pattern
  + a `statusMessage` pointing at the safer one.

Both are deny-and-suggest. Only Gemini does silent-corrective-rewrite.

## Source

- `docs/shell-skills-research.md` § 4 lines 273–294 (Gemini hook contract,
  `hookSpecificOutput.tool_input` semantics) + § closing observations
  lines 436–442 ("Expect to see ShellHarden-via-hook patterns become
  standard on Gemini before they reach the other two").
- Gemini hook protocol: `developers.googleblog.com/tailor-gemini-cli-to-your-workflow-with-hooks/`.
