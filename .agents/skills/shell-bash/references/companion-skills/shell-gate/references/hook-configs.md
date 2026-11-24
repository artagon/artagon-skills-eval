# Historical per-CLI hook examples

These April/May 2026 research examples are not verified-current or installable
configuration. Do not copy, install or commit them without an explicit project
integration task and fresh provider-native documentation checks. Inspect the
existing project and user configuration without exposing secret fields.

Verify each client's actual event names, input/output schema, supported
decisions, exit semantics, tool identity and approval behavior independently.
The old research's shared-protocol claim is not a current compatibility
guarantee. Gate host Bash 4.4+ is separate from target scripts; file checks are
read-only, command screening is advisory, and unsupported targets fail.

The retained blocks below are historical evidence for review, not instructions
to execute. Native Zsh cannot be certified with Bash-mode ShellCheck. A
warning-only diagnostic threshold omits SC2086 info findings.

## Claude Code

`.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "p=$(jq -r '.tool_input.file_path'); ${CLAUDE_PROJECT_DIR}/plugins/artagon-shell/skills/shell-gate/scripts/shell-gate.sh \"$p\""
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(rm -rf *)",
            "command": "jq -n '{hookSpecificOutput:{hookEventName:\"PreToolUse\",permissionDecision:\"deny\",permissionDecisionReason:\"rm -rf gated by shell-gate\"}}'"
          }
        ]
      }
    ]
  },
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Bash(rm -rf *)",
      "Bash(git push --force *)"
    ],
    "allow": [
      "Bash(shellcheck:*)",
      "Bash(shfmt:*)",
      "Bash(shellharden:*)",
      "Bash(git status)",
      "Bash(git diff:*)"
    ]
  }
}
```

Notes from `docs/shell-skills-research.md` § 4 lines 209–248:

- `permissionDecision: "deny"` in stdout JSON blocks even under
  `--dangerously-skip-permissions` / `bypassPermissions` mode. Bug #23284
  documents that `exit 2` is NOT always sufficient — prefer `deny`.
- The `if: "Bash(rm -rf *)"` clause (since v2.1.85) uses permission-rule
  syntax for argument-level filtering, so the hook only spawns when needed.
- Permissions evaluate **deny → ask → allow, first-match wins, deny always
  beats allow**. `Bash(ls *)` matches `ls -la` but not `lsof` (word
  boundary); `Bash(ls*)` matches both.
- `permissions.deny` rules restrict only the Bash tool's input string. They
  do NOT constrain child processes spawned by an allowed command. Pair
  with sandbox (`/sandbox` on macOS, bwrap on Linux).

## Codex CLI

`.codex/config.toml`:

```toml
sandbox_mode = "workspace-write"
approval_policy = "on-request"

[features]
hooks = true

[[hooks.PreToolUse]]
matcher = "^Bash$"

[[hooks.PreToolUse.hooks]]
type = "command"
# shell-gate.sh handles both file payloads and run-command payloads via
# --hook-stdin. Codex PreToolUse Bash sends {"tool_input":{"command":"..."}};
# the dispatch routes to check_destructive_command_string() on the string.
command = '${CLAUDE_PROJECT_DIR:-$PWD}/plugins/artagon-shell/skills/shell-gate/scripts/shell-gate.sh --hook-stdin'
timeout = 30
statusMessage = "Gating shell command"

[shell_environment_policy]
inherit = "none"
set = { PATH = "/usr/local/bin:/usr/bin:/bin" }
exclude = ["AWS_*", "AZURE_*", "GCP_*", "GITHUB_TOKEN", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]

# Organization-level hard-deny prefixes (admin-enforced, separate from hooks):
[[rules.requirements]]
pattern = "^rm -rf /"
decision = "deny"
rationale = "Blanket /-wipe — refuse unconditionally"

[[rules.requirements]]
pattern = "^git push --force "
decision = "deny"
rationale = "Use --force-with-lease instead"
```

Notes from `docs/shell-skills-research.md` § 4 lines 252–271:

- Codex hooks (since late 2025, `[features] hooks = true`) cover
  `SessionStart`, `PreToolUse`, `PermissionRequest`, `PostToolUse`,
  `UserPromptSubmit`, `Stop`.
- **PreToolUse fires only for the Bash tool** — Read/Write/Edit/MCP do not
  trigger it. For post-edit shell-gating, run client-side after the edit
  lands.
- Codex parses but **rejects** `updatedInput` / `updatedMCPToolOutput` in
  hook output. Hooks can deny but cannot mutate.
- `rules.requirements` is admin-enforced org-wide policy, separate from
  hooks. Use it for blanket hard-deny rules.
- The `shell_environment_policy` sanitizes env before subprocess launch —
  `inherit = "none"` + explicit `set` is the secure default.

## Gemini CLI

`.gemini/settings.json`:

```jsonc
{
  "tools": {
    "sandbox": "docker",
    "core": [
      "read_file",
      "write_file",
      "glob",
      "search_file_content",
      "list_directory",
      "run_shell_command(git)",
      "run_shell_command(npm)",
      "run_shell_command(shellcheck)",
      "run_shell_command(shfmt)",
      "run_shell_command(shellharden)",
      "run_shell_command(bats)"
    ],
    "exclude": [
      "run_shell_command(rm)",
      "run_shell_command(curl)",
      "run_shell_command(wget)",
      "run_shell_command(sudo)"
    ]
  },
  "security": {
    "folderTrust": { "enabled": true },
    "disableYolo": false,
    "redactEnvVars": true,
    "alwaysRedactEnvVars": ["GITHUB_TOKEN", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
  },
  "hooks": {
    "BeforeTool": [
      {
        "matcher": "run_shell_command",
        "hooks": [
          {
            "type": "command",
            "command": "${GEMINI_PROJECT_DIR}/plugins/artagon-shell/skills/shell-gate/scripts/shell-gate.sh --hook-stdin"
          }
        ]
      }
    ]
  }
}
```

Notes from `docs/shell-skills-research.md` § 4 lines 273–294:

- Gemini event names: `BeforeTool`, `AfterTool`, `BeforeAgent`, `AfterAgent`,
  `BeforeModel`, `AfterModel`, `BeforeToolSelection`, `SessionStart`,
  `SessionEnd`, `UserPromptSubmit`, `Notification`, `PreCompress`.
- `gemini hooks migrate --from-claude` maps Claude event names.
- **Unique to Gemini**: `hookSpecificOutput.tool_input` *merges with and
  overrides* the model's args before execution. See
  `gemini-hook-mutation-patterns.md`.
- **Critical gotcha** (Gemini Issue #18807): `tools.core` is an allowlist
  for **all** built-in tools, not just shell. Setting `core:
  ["run_shell_command"]` accidentally disables `read_file`, `write_file`,
  `glob`, etc. Always include the other read/write tools explicitly (as
  in the snippet above).
- `tools.exclude` is **documented explicitly as NOT a security boundary** —
  command-prefix matching is bypassable through `eval`, base64-decoded
  command substitution, etc. Use `tools.core` (allowlist) + sandbox +
  hooks for real safety.
- Enterprise lockdown keys (system-settings-only): `disableYoloMode`,
  `disableExtensions`, `disableMcpServers`, `adminMcpServers`,
  `requiredMcpServers`.

## Universal AGENTS.md

The single source of truth for shell rules across all three CLIs is
`AGENTS.md` (with `CLAUDE.md` and `GEMINI.md` as symlinks). The ≤60-line
shell block to drop in is in
`agents-md-template.md`.

## Source

`docs/shell-skills-research.md` § 4 lines 207–312 (per-CLI integration
mechanisms) + § 6 lines 375–423 (recommended layout per CLI).
