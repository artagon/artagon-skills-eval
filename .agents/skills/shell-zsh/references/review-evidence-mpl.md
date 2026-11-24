<!-- SPDX-License-Identifier: MPL-2.0 -->
# Shell review evidence

Modified adaptation of `rikdc/ai-skills` shell-script-reviewer,
`c7bb0845c818519570e92f4e176f4fa32cf5a7df`,
`plugins/dev-skills/skills/shell-script-reviewer/SKILL.md`.
Artagon changed this file on 2026-11-06: reduced it to dialect detection,
structured findings and missing-tool evidence; removed upstream wrappers,
auto-fix behavior and blanket removal of strict options. This file's Source
Code Form is available under MPL-2.0. A copy is supplied as
`LICENSE.upstream-rikdc-shell-reviewer` in this directory; the license is
also available at https://mozilla.org/MPL/2.0/.

1. Establish the dialect from the declared invocation and target contract,
   then check shebang, file role and syntax for contradictions. File suffix
   is a hint rather than sufficient evidence. Unknown dialect stays an
   explicit assumption or missing fact.
2. For every finding, report exact file and line, severity, category,
   triggering scenario, consequence, concrete fix and supporting evidence.
   Distinguish security, correctness, portability and style findings.
3. Record every attempted tool's version, dialect, exit status and actual
   coverage. When a tool is missing, unsupported or unable to inspect a
   dependency, label the coverage reduction. An empty result or wrapper
   exit zero does not prove that analysis ran successfully.
4. For native Zsh, use its own semantics and interpreter. Bash-mode lint
   cannot certify option behavior, indexing, expansion or interactive roles.
5. Retain intentional failure policy and review its error paths. Do not
   remove `-e`/`-u` merely to follow the upstream policy, and do not rely on
   strict options instead of checking critical statuses.
6. Review only the authorized source closure. Reading sourced dependencies,
   running fixtures and applying proposed fixes are separate scope choices.
   A review finding alone does not authorize edits or execution.
