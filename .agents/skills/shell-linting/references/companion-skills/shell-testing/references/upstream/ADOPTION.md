# Shell source adoption

Recorded 2026-11-06. This adoption preserves five task workflows and adds
three target selectors: Bash, editioned POSIX sh and native Zsh. Sources
are absorbed into those eight capabilities rather than published as
duplicate upstream-named skills.

The machine-readable record is [adoption-sources.json](adoption-sources.json).
It covers all nine primary skill files, two supplementary skill references
and the adjacent awesome-copilot instruction file from the research.
“Adopted” means the source has an explicit disposition and destination;
it does not mean every source was copied or every upstream claim accepted.

| Source | Disposition and concrete destination |
| --- | --- |
| ZaguanLabs/zsh-expert-skill, Apache-2.0 | Selected modified context, options, role and version guidance in `skills/shell-zsh/SKILL.md` and `references/zsh-profiles.md`; full package and executable verifiers not imported |
| sjinks/ai-skills shell-portability, MIT | Modified target/utility contract and bounded verdict in all three selectors and especially `skills/shell-posix/references/posix-profiles.md`; elaborate handoff protocol omitted |
| posidoni/shell-skill, MIT | Modified dialect/example organization in the selectors and their eval cases; all references are inside each selector; upstream external reference layout and Bash-only example proof not imported |
| rikdc/ai-skills shell-script-reviewer, MPL-2.0 | Modified finding schema and reduced-coverage discipline isolated in each new selector's `references/review-evidence-mpl.md`, carrying an MPL notice and full license; wrapper scripts and blanket strict-option policy not imported |
| abdullahkhawer/devops-skills bash-linting, Apache-2.0 | Deduplicated into original local check/diff-first, existing-config-aware linting guidance in `skills/shell-linting/SKILL.md` and `references/ci-integration.md`; no upstream file content copied |
| wshobson bash-defensive-patterns, MIT | Existing absorbed lineage in `shell-defensive/references/defensive-patterns.md`; current survey pin is comparison evidence, not a claimed new import |
| wshobson bats-testing-patterns, MIT | Existing absorbed lineage in `shell-testing/references/bats-patterns.md`; no duplicate skill or new raw import |
| wshobson shellcheck-configuration, MIT | Existing absorbed lineage in `shell-linting/references/sc-codes.md` and linting guidance; no duplicate skill or new raw import |
| pvillega/claude-templates bash-hardening, grant unresolved | External comparison only, linked in the Bash source card; no text or code copied. Local error/version guidance is original and grounded in GNU documentation |
| cstrahan/claude-plugins shell, grant unresolved | External comparison only, linked in the Bash source card; no text or code copied. Target interpreter guidance is original and grounded in official documentation |
| agiacalone/unix-conventions, GPL-3.0 repository evidence | External comparison only, linked in the POSIX source card, pending per-file provenance for the mixed-source bundle; no material copied |
| github/awesome-copilot shell instructions, MIT | External format comparison in the POSIX source card and workflow target contracts; an instruction file rather than another skill; no instruction file copied |

Every source has an immutable survey revision in the JSON record. Those
pins preserve source identity. They do not establish whole-repository
audits, deployed support, license compatibility for an arbitrary downstream
combination or acceptance of the current upstream version.

## License and attribution boundaries

Original Bash/POSIX selector prose and MIT adaptations use MIT; the native
Zsh selector and modified Zaguan guidance use Apache-2.0. Each
`review-evidence-mpl.md` remains MPL-2.0, separate from surrounding files.
The new root `LICENSE.upstream-*` grants are also copied inside each
selector where needed, together with `references/NOTICE.adoption` and
source cards. Copyright notices from MIT inputs are retained.

License text extracted from research evidence has normalized rendering;
the Apache text uses canonical license wording with the upstream template
placeholder. These are full grants, not asserted byte-exact upstream
license files. No additional Zaguan NOTICE file was established by the
research inventory. Existing inherited legal/provenance files remain the
record of the earlier wshobson absorption.

## Evidence boundaries

The cache includes exact bodies and Git blob IDs for eight inspected
`SKILL.md` files. Supporting-source excerpts were not all byte-exact;
they are review evidence, not a vendored archive. The pinned Zaguan SKILL,
version guide and license were read using native public fetch for this
adoption. No cloned repository or downloaded executable ran.

Source audit does not establish native behavior. In particular:

- Zaguan's bounded 5.9.2 Linux results do not establish 5.9, macOS,
  all-module or arbitrary PTY compatibility. Its 5.9.2 feature attribution
  was corrected to 5.9.1 using official release notes.
- Upstream Bash-run “POSIX” examples do not prove dash/ash behavior.
- ShellCheck has no native Zsh mode and no exact Bash minimum/POSIX edition
  selector. shfmt Zsh support remains incomplete.
- A syntax check, missing-tool exit zero or skipped target is not a runtime
  pass. Sourced callers, startup files, utility builds and interactive roles
  require distinct verification cells.

The new eval sources were written before selector wording: three behavior
cases and eight positive/eight near-miss routing prompts per selector.
Baseline, stochastic provider routing and cross-version runtime acceptance
remain unrun unless recorded by a separate execution receipt. No model
performance claim follows from eval-file presence.
