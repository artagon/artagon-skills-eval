# Native Zsh profiles and execution boundaries

Modified adaptation of ZaguanLabs/zsh-expert-skill at
`cf2731a05cd6c8961d13b0f3faf79c49559fad32`, Apache-2.0. Artagon shortened the
contract, corrected the 5.9.1 feature attribution, and separated startup,
execution and coverage claims. The full license is bundled with this skill.

## Version and capability matrix

| Target | Decision |
| --- | --- |
| 5.9 | Use the documented 5.9 feature set; do not infer later features from a current manual or upstream 5.9.2 tests |
| 5.9.1 | Official release notes introduce real-time signal support where available, `kill -q`/`-L`, and `_as_if` here |
| 5.9.2 | Select it explicitly when it is the project floor; its upstream test claims do not establish 5.9, macOS or all-module coverage |
| Development revision | Require an exact revision and experimental label; isolate new syntax from older parsers |

The [official release notes](https://zsh.sourceforge.io/releases.html)
govern the 5.9.1 attribution. The pinned upstream version guide assigns
those additions to 5.9.2; that attribution is intentionally corrected here.
Use Zsh's documented `is-at-least` helper after appropriate autoload setup
or another numeric-aware version check, rather than lexical string order.
Version checks do not establish that a module, contributed function,
terminal capability or external utility is present in a particular build.

When newer syntax is not parseable on the minimum shell, place it in a
separate file selected only after the capability/version decision. An `if`
branch around syntax that the old parser must read is insufficient. Do not
introduce `eval` of untrusted data as a compatibility workaround.

## Native language and option state

- Native indexed arrays normally start at one; `KSH_ARRAYS` changes the
  indexing contract. Ordinary native scalar parameter expansion does not
  perform IFS word splitting; `SH_WORD_SPLIT`, expansion flags and deliberate
  split forms change that behavior. Keep argument boundaries explicit.
- For reusable ordinary functions, `emulate -L zsh` establishes a known
  option baseline and enables option/pattern/trap locality in the enclosing
  function. It does not localize arbitrary variables, cwd, descriptors,
  aliases or hook registrations. At top level there is no enclosing
  function to supply that locality boundary.
- Completion functions inherit compsys options. Preserve that environment
  instead of resetting it with an unconditional emulation preamble.
- Autoload has parse-time alias and `fpath` concerns. Set the intended
  autoload contract, account for `-U` alias suppression where appropriate,
  and test the actual load/invocation path rather than only sourcing a file.
- Treat `eval`, evaluation expansion, `source`, prompt substitution and
  directory-local code as execution boundaries. Do not evaluate untrusted
  text to manufacture a native-shell idiom.

These details follow the official
[parameters](https://zsh.sourceforge.io/Doc/Release/Parameters.html),
[expansion](https://zsh.sourceforge.io/Doc/Release/Expansion.html),
[options](https://zsh.sourceforge.io/Doc/Release/Options.html) and
[builtins](https://zsh.sourceforge.io/Doc/Release/Shell-Builtin-Commands.html).

## Role, startup and lifecycle

Name the owned state for plugins, widgets and prompts. Add and remove only
the component's own hook registrations; avoid replacing singleton hooks
that another component owns. Set `fpath` before `compinit` and preserve
`compaudit` permission checks. `compinit -u` is not a compatibility fix.
Async widgets need descriptor cleanup, stale-result rejection and bounded
callbacks, with PTY tests for visible behavior.

`zsh -f -n FILE` parses the target without executing its body. The global
zshenv can still execute under `-f`, as documented in
[startup files](https://zsh.sourceforge.io/Doc/Release/Files.html).
Build/install paths vary. A temporary ZDOTDIR changes user startup lookup;
it is neither an OS sandbox nor proof that a check has no host effects.

Native Zsh and sh emulation are separate contracts. Invocation-time
`--emulate sh` performs setup beyond an in-shell `emulate sh`. Zsh's
[compatibility documentation](https://zsh.sourceforge.io/Doc/Release/Invocation.html#Compatibility)
does not promise complete emulation or POSIX compliance.

## Validation cells and limits

1. Parse with the actual minimum native Zsh, recording options and startup
   exposure. Do not relabel Zsh as Bash to pass ShellCheck.
2. Execute only explicitly scoped smoke fixtures under the intended host or
   containment boundary, with bounded runtime and deterministic cleanup.
3. Test sourced caller state, autoload parsing and module-dependent behavior
   in their intended process. A missing module is missing coverage.
4. Use a PTY for completion, keymaps, ZLE, prompts and interactive startup.
   A noninteractive syntax check does not validate those roles.

shfmt 3.13+ has incomplete Zsh support; the inspected 3.14.1 supports
`-ln zsh`. Parser/formatter acceptance does not replace native execution.
ShellCheck has no native Zsh mode. Record tool versions and report parser
limitations rather than discarding valid native syntax for a green gate.

The inspected upstream semantic suite reports bounded 5.9.2 Linux results
with optional-module skips. It was not imported. Its top-level failure
exits can bypass an `always` cleanup block, so it must not be treated as a
safe universal verifier. Artagon acceptance needs its own actual minimum,
current, OS/utility and PTY cells; none is established by this guidance.
