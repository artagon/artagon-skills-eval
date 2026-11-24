---
name: shell-posix
description: Selects POSIX 2017/2024 sh contracts for dash/ash and OS utilities. Use when checking portability or bashisms. Do not use for Bash-only or native Zsh work.
license: MIT
compatibility: Read-only profile selection needs no binary or network. Verification needs each declared dash, ash, BusyBox or other sh implementation and actual OS utilities. ShellCheck, shfmt and checkbashisms are optional static tools. No MCP server is required.
metadata:
  owner: artagon
  version: "0.1.0"
  status: experimental
  verified: "2026-11-06"
---

# POSIX shell target selection

Skill marker: `artagon-shell/shell-posix/v1`.

This selector fixes the standards edition, implementation and utility
contract for portable shell work. It supplies that contract to the
authoring, defensive, testing, linting and gate workflows.

## Target contract

1. Record POSIX.1-2017 or POSIX.1-2024 explicitly, executable versus sourced
   role, invocation, named interpreter versions, and actual OS utilities.
   A `/bin/sh` pathname or “ash” label alone is not enough.
2. If the edition is unstated, use 2017 as a conservative analysis
   assumption and say so. Do not invent an implementation support claim.
3. Read [POSIX profiles](references/posix-profiles.md) for edition
   boundaries, utility dependencies and native test cells.
4. Keep required failure behavior. When the deployment lacks a required
   feature, provide a behavior-preserving alternative, reject the target
   or ask for a target change. Never silently remove failure detection.
5. State the portability verdict against the declared matrix and show
   missing evidence. A generic green `sh` linter result is insufficient.

## Evidence and provenance

[Sources and adaptations](references/sources.md) identifies the licensed
target-contract and example-design inputs. The isolated
[MPL review guide](references/review-evidence-mpl.md) supplies a finding
format and reduced-coverage discipline. Other files retain their stated
licenses. No upstream executable verifier is shipped.

The `evals/` files specify behavior and near-miss routing. Provider-level
invocation and grading remain unverified until those cases run.

## Harmless invocation

Example: `shell-posix report --edition 2017 --targets dash,busybox-ash`.

This is a skill request, not a shipped executable. Summarize the supplied
target and missing version/utility facts. Run no command, source no file
and make no edit for this report. State `mutations=none` and
`runtime=not-run`.

## Output contract

Return the standards edition; interpreter versions and invocation; file
role; OS and utility matrix; findings with locations and replacements;
caller-state effects; actual syntax/static/runtime checks; missing cells;
and a portability verdict limited to the evidence. Distinguish confirmed
behavior, documented requirements and unverified assumptions.
