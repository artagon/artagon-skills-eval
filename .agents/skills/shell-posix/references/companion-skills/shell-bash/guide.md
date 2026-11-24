---
name: shell-bash
description: Selects Bash 3.2/4.0/4.3/4.4/5.x contracts. Use when checking Bash version gates, sourced state or error semantics. Do not use for POSIX or native Zsh work.
license: MIT
compatibility: Read-only profile selection needs no binary or network. Verification needs the actual declared Bash versions and OS utilities; ShellCheck and shfmt are optional static tools. No MCP server is required.
metadata:
  owner: artagon
  version: "0.1.0"
  status: experimental
  verified: "2026-11-06"
---

# Bash target selection

Skill marker: `artagon-shell/shell-bash/v1`.

This selector supplies Bash version and execution-context decisions to the
authoring, defensive, testing, linting and gate workflows. It selects a
contract; it does not confer compatibility by loading the skill.

## Target contract

1. Read the declared target and invocation before choosing features. Record
   the minimum Bash version, executable versus sourced role, interpreter
   path or PATH selection, OS and utility implementations. Preserve existing
   public names and launch contracts.
2. Use [Bash profiles](references/bash-profiles.md) for 3.2, 4.0, 4.3, 4.4
   and 5.x feature floors, numeric gates and sourced-state boundaries.
3. Distinguish option policy from error correctness. Keep intentional
   fail-closed behavior. Neither adding strict options nor removing them
   substitutes for explicit handling of critical failures.
4. Apply the general workflow requested by the task after fixing its Bash
   profile. A formatter-only, test-fixture-only or hook-wiring task with an
   already settled profile belongs to the corresponding workflow.
5. Report static, minimum-version runtime and current-version runtime
   evidence separately. An unavailable target stays unverified.

## Evidence and provenance

[Sources and adaptations](references/sources.md) identifies licensed
adaptation inputs and external references. The isolated
[MPL review guide](references/review-evidence-mpl.md) supplies a finding
format and reduced-coverage discipline. It does not change the license of
the other files. No upstream wrapper, installer or verifier is shipped.

The behavior and routing cases under `evals/` are specifications. Their
presence is not evidence that any provider loaded this skill or passed a
case.

## Harmless invocation

Example: `shell-bash report --minimum 3.2 --role sourced --os macos`.

This is a skill request, not a shipped executable. Return the profile,
feature conflicts and proposed checks from the supplied context. Run no
command, source no file and make no edit for this report. State
`mutations=none` and `runtime=not-run`.

## Output contract

Return the minimum and observed Bash versions; invocation and file role;
OS/utility dependencies; unsupported features with locations; caller-state
effects; proposed fixes; actual static and runtime checks with exact
versions; missing coverage and the compatibility verdict. Keep assumptions
and unverified cells explicit. A plan is not a runtime pass.
