# Historical OS sandbox examples

The following April/May 2026 research recipes are not verified-current client
defaults, portable profiles or proof of containment. Configuring a sandbox or
installing a hook requires an explicit integration task. Inspect the actual
platform, client version, mounts, inherited descriptors, network and writable
paths before proposing a bounded configuration.

Treat shell-pattern screening as advisory and test isolation with inert denied
operations inside a disposable fixture. Do not execute destructive examples or
launch an autonomous loop to validate this document. Fixed /tmp profile paths
and broad writable temp directories in the historical examples need local
ownership/scope review before any use. Bash preambles below describe the
launcher, not every target's shell language or minimum version.

The three-layer model from `docs/shell-skills-research.md` § 1:

1. **Soft layer** — AGENTS.md / SKILL.md / GEMINI.md prompt-level rules (model may ignore)
2. **Application layer** — permission allow/deny lists in the CLI (bypassable via shell tricks; CVE-2025-66032 documents 8 ways)
3. **OS layer** — Seatbelt / bwrap+seccomp / Docker — the only layer that actually contains a misbehaving agent

The 2025–2026 incident log is unambiguous evidence that no soft layer is
sufficient on its own: Wolak's `rm -rf /` (Oct 2025), the Reddit Mac
home-directory wipe (Dec 9 2025), Replit's prod-DB deletion, Amazon Q's
shipped-to-1M-users wipe, and CVE-2025-66032's eight deny-list bypasses
(sed `e` command, bash variable construction, git arg abbreviation,
`node -e`, `python3 -c`, base64 substitution, eval-via-aliases).

Never run an autonomous loop (Ralph, agent-safehouse, etc.) on the host
without a sandbox.

## macOS — Seatbelt via `sandbox-exec`

`sandbox-exec` is built into macOS. Profiles are SBPL (Sandbox Policy
Language). The `permissive-closed` profile blocks outbound network +
filesystem writes outside a writable allowlist:

```bash
# Codex CLI ships a baseline profile at:
#   codex-rs/core/src/seatbelt_base_policy.sbpl
# For a Ralph loop with workspace-write, extend that with:

cat > /tmp/ralph.sbpl <<'EOF'
(version 1)
(deny default)
(allow process-fork)
(allow file-read*)
(allow file-write*
  (subpath "/Users/me/work/ralph-target")
  (subpath "/tmp")
  (subpath "/var/folders"))
(allow network*
  (remote tcp "127.0.0.1:*"))   ; localhost only
(deny network-outbound (remote ip "*:*"))
EOF

sandbox-exec -f /tmp/ralph.sbpl ralph-loop --target my-task.md
```

Codex CLI uses Seatbelt by default on macOS with dynamic SBPL profiles
generated from `sandbox_mode` config. Claude Code's `/sandbox` slash
command also wires Seatbelt.

## Linux — bwrap + seccomp

`bwrap` (Bubblewrap) is the userspace sandbox library that Flatpak uses.
Codex CLI uses it by default since v0.115; Landlock is retained as a
legacy fallback. seccomp blocks `connect`/`bind`/`sendto` when network is
disabled.

```bash
bwrap \
  --ro-bind / / \
  --bind ~/work/ralph-target ~/work/ralph-target \
  --tmpfs /tmp \
  --proc /proc --dev /dev \
  --unshare-all \
  --share-net \
  --setenv RALPH_SANDBOX 1 \
  -- \
  ralph-loop --target my-task.md
```

For tighter sandboxes (no network at all):

```bash
bwrap --ro-bind / / --tmpfs /tmp --unshare-all --new-session -- ralph-loop
```

`--unshare-all` creates a new user/mount/PID/IPC/UTS namespace; the
process can't see other PIDs, can't write outside the binds, can't reach
the network unless explicitly granted with `--share-net`.

For seccomp filters on top of bwrap (e.g. block `ptrace`, `mount`,
`kexec_load`), `firejail` ships profiles, or write custom seccomp BPF
and apply with `prctl(PR_SET_SECCOMP, …)` from a wrapper.

## Cross-platform — Docker

For a single recipe across macOS, Linux, and WSL2:

```bash
docker run --rm -it \
  --read-only \
  --tmpfs /tmp:exec \
  --tmpfs /var/tmp \
  --volume "$PWD:/work" \
  --workdir /work \
  --network none \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --user "$(id -u):$(id -g)" \
  ralph-runner:latest \
  ralph-loop --target my-task.md
```

Flags:
- `--read-only` makes the container FS read-only (except mounted volumes)
- `--tmpfs /tmp:exec` provides a writable, in-memory `/tmp` (binaries OK)
- `--network none` disables outbound network entirely
- `--cap-drop ALL` strips all Linux capabilities
- `--security-opt no-new-privileges` blocks setuid escalation
- `--user "$(id -u):..."` runs as the host user, not root

For a Ralph loop that needs network (to fetch packages, hit APIs),
replace `--network none` with `--network bridge` and add an egress
firewall rule via `iptables` or Docker's built-in network policies.

## Ralph-loop integration

Geoffrey Huntley's playbook (`ghuntley.com/ralph`, `ghuntley.com/loop`)
explicitly requires:

- Claude Code: `--dangerously-skip-permissions`
- Codex: `--full-auto` or `--dangerously-bypass-approvals-and-sandbox`
- Gemini: `--yolo`

Those flags REMOVE the application-layer deny-list. The sandbox is what
contains a runaway then. `mikeyobrien/ralph-orchestrator` is the most
polished multi-backend implementation — uses Claude Code, Q Chat, Gemini
CLI, and any ACP-compliant agent, uses a Stop Hook intercepting exit
code 2 to re-inject the prompt, and detects task end via
`- [x] TASK_COMPLETE`.

A complete Ralph wrapper (Linux, network-disabled, with shell-gate
enforcement inside the sandbox):

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
target="${1:?usage: $0 <target.md>}"

# Pre-flight: gate the target file itself
plugins/artagon-shell/skills/shell-gate/scripts/shell-gate.sh "$target"

# Run loop inside sandbox
bwrap \
  --ro-bind / / \
  --bind "$PWD" "$PWD" \
  --tmpfs /tmp \
  --proc /proc --dev /dev \
  --unshare-all \
  --new-session \
  --setenv ANTHROPIC_API_KEY "$ANTHROPIC_API_KEY" \
  -- \
  ralph-loop --backend claude --target "$target" \
             --post-hook plugins/artagon-shell/skills/shell-gate/scripts/shell-gate.sh
```

## Source

- `docs/shell-skills-research.md` § 1 (lines 1–62, layered security model) +
  § 4 (per-CLI sandbox implementations) + § 6 line 434 ("Run Ralph in a
  hardened sandbox").
- Codex CLI Seatbelt/Landlock/bwrap+seccomp: Simon Willison's
  24 Dec 2025 deep dive + DeepWiki `openai/codex/5.6-sandboxing-implementation`.
- Pierce Freeman's "A Deep Dive on Agent Sandboxes" at
  `pierce.dev/notes/a-deep-dive-on-agent-sandboxes`.
- Anthropic Docker template + `agent-safehouse.dev`.
