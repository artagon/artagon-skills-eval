# Bash profiles and evidence

This is original Artagon guidance informed by the GNU Bash documentation
and the attributed adaptation inputs in the skill's source card. These
profiles are selection rules; no listed target is guaranteed by this file.

| Declared floor | Available baseline | Excluded from that baseline |
| --- | --- | --- |
| 3.2 | Indexed arrays, `[[ ]]`, Bash `local`, `pipefail`, ERR/EXIT traps | Associative arrays, `mapfile`, namerefs, `inherit_errexit` |
| 4.0 | Associative arrays and `mapfile` | Namerefs, `mapfile -d`, `inherit_errexit` |
| 4.3 | Namerefs in addition to earlier features | `mapfile -d`, `inherit_errexit` |
| 4.4 | `mapfile -d`, `inherit_errexit`; changed nounset handling for arrays without assigned elements | Later features need their own introduction history and minimum-version test |
| 5.x | Earlier floors plus features documented for the exact selected 5.x minimum | “5.x” does not mean that every feature in the latest manual exists in 5.0 |

Feature introductions are documented in the
[GNU maintainer change history](https://tiswww.case.edu/php/chet/bash/CHANGES)
and the [4.4 announcement](https://lists.gnu.org/archive/html/info-gnu/2016-09/msg00012.html).
Do not select a minimum from the current manual alone.

## Major-first version gates

`BASH_VERSINFO[0]` is the major number and `[1]` is the minor number, as
documented in [Bash variables](https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html).
For a Bash 4.4 floor, the numeric predicate is:

```bash
(( BASH_VERSINFO[0] > 4 ||
  (BASH_VERSINFO[0] == 4 && BASH_VERSINFO[1] >= 4) ))
```

This decision accepts 4.4 and 5.0 and rejects 3.2, 4.0 and 4.3. The wrong
predicate `major >= 4 && minor >= 4` rejects valid 5.0 through 5.3 releases.
Use an explicit failure branch at an executable entry point. A sourced
library returns a failure according to its API rather than exiting its
caller. New syntax must be parseable by the older shell before a runtime
guard can help; isolate unsupported syntax in a separately selected file.

## Error and caller-state contract

- `set -e` and ERR traps have documented suppression contexts, including
  tested functions, nonfinal AND/OR commands and pipeline contexts. Review
  those paths against the [set builtin](https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html)
  and [trap rules](https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html).
- `-E` extends ERR trap inheritance. It does not make the trap run in
  contexts that suppress ERR. `inherit_errexit` changes command-substitution
  option inheritance; it is not complete error propagation.
- Declaration builtins can hide a substitution status. Declare the local
  separately and handle the assignment failure where its status matters.
- Sourcing runs in the caller. Preserve or explicitly own options, shopt
  state, traps, IFS, working directory, positional parameters and exported
  values. A library shebang does not choose the caller's interpreter.
- Keep project strict-mode policy where compatible with the target and
  role; do not copy an executable preamble into a library without a state
  contract. Restoring only `set -e` is insufficient if it was initially off.

## Validation cells

Record interpreter path and full version, file role, options and actual
utility implementations for every executed cell. Minimum-version execution
is required for a minimum-version claim. A newer Bash compatibility option
is not an older interpreter.

Use explicit Bash dialects for static tools, for example `shellcheck -s
bash FILE` and `shfmt -ln bash -d FILE`. Neither tool selects a Bash 3.2
language floor. Keep informational quoting diagnostics visible when they
are part of the gate; a warning-only threshold omits SC2086.

Bats runs in Bash. Invoke the target Bash explicitly for executable tests;
source libraries only in the intended target process and compare caller
state before and after. Include failure paths, filenames with whitespace,
empty arrays and tested-function contexts. No network or destructive
fixture is needed for these checks.

Google Shell Style is the Bash style baseline, including its `/bin/bash`
example, 80-column guidance and advice to reconsider shell for larger or
complex programs. An `env bash` launch contract is a project choice and
does not establish a version. Utility portability remains separate from
the Bash language floor.
