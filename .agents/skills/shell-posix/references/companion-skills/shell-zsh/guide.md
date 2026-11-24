---
name: shell-zsh
description: Selects native Zsh 5.9/5.9.1/5.9.2 contracts. Use when checking options, autoload, startup, completion or ZLE semantics. Do not use for POSIX or Bash work.
license: Apache-2.0
compatibility: Read-only profile selection needs no binary or network. Verification needs each declared native Zsh version, relevant modules and OS utilities; interactive checks need a PTY. shfmt Zsh support is optional and incomplete; ShellCheck has no native Zsh mode. No MCP server is required.
metadata:
  owner: artagon
  version: "0.1.0"
  status: experimental
  verified: "2026-11-06"
---

# Native Zsh target selection

Skill marker: `artagon-shell/shell-zsh/v1`.

This selector supplies native Zsh contracts to authoring, defensive,
testing, linting and gate workflows. It adapts selected ZaguanLabs guidance
with corrected feature floors and explicit startup/execution limits.

## Target contract

1. Record minimum and observed Zsh versions, native mode versus deliberate
   emulation, OS/utilities, optional modules, and role: executable, sourced
   library, autoload function, startup file, plugin, completion, ZLE widget
   or prompt. Do not infer the target from the user's login shell.
2. Read [native profiles](references/zsh-profiles.md) for 5.9/5.9.1/5.9.2
   boundaries, option semantics, caller state and role-specific checks.
3. Preserve caller-owned options, aliases, traps, hooks, keymaps, prompts
   and descriptors. An autoloaded function and a top-level startup file
   have different locality boundaries.
4. Keep syntax, explicit smoke execution, semantic fixtures and PTY evidence
   separate. Never turn a parse-only request into execution automatically.
5. Use native Zsh review and tests. Bash-mode ShellCheck cannot establish
   native semantics. A missing native lane remains missing coverage.

## Evidence and provenance

[Sources and adaptations](references/sources.md) identifies pinned inputs,
license notices and upstream limitations. The isolated
[MPL review guide](references/review-evidence-mpl.md) supplies a finding
format and reduced-coverage discipline. No upstream verifier, semantic
suite, installer or framework hook is shipped or executed by this skill.

Behavior and routing cases under `evals/` are specifications. No native
provider discovery or full version/platform acceptance is implied.

## Harmless invocation

Example: `shell-zsh report --minimum 5.9 --role autoload --mode native`.

This is a skill request, not a shipped executable. Return the supplied
contract, option/startup risks and proposed checks. Run no command, source
no file and make no edit for this report. State `mutations=none` and
`runtime=not-run`.

## Output contract

Return minimum/observed versions; native/emulation mode; file role and
framework; option and caller-state assumptions; utilities/modules;
findings with locations and fixes; actual syntax, smoke, semantic and PTY
checks; startup exposure; missing cells and compatibility verdict. Label
upstream claims and local observations separately.
