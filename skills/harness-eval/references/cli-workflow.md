# CLI Workflow Reference (`harness-eval`)

## JSON Envelope (`harness-eval-envelope/v1`)

Every `--output json` invocation prints a single JSON object to `stdout`:

- **Success (`ok: true`, `exit_code: 0`)**:
  - `schema_version`: `"harness-eval-envelope/v1"`
  - `ok`: `true` (strictly `exit_code == 0`)
  - `command`: subcommand name (`auth`, `preflight`, `freeze`, `run`, `analyze`, `status`, `trace-query`, `trace-export`, `waza-export`, `waza-import`, `optimize-gepa`, `nix-check`, `probe`)
  - `exit_code`: `0`
  - `reason_code`: `null`
  - `mutations`: `"none"` for read-only, `--dry-run`, and network `trace-export` calls; `"frozen_manifest"` for `freeze`; `"campaign_dir"` for live `run` and `analyze`; `"export_file"` or `"export_dir"` for file/directory-writing `trace-export` and `waza-export`; stringified path list (or `"protocol_file"` fallback, with path list in `data.mutations`) for `waza-import`; and `"candidate_bundle"` for `optimize-gepa`
  - `data`: subcommand payload (`schedule`, `summary`, `checks`, `frozen_manifest_path`, or `rows`)
- **Non-Zero Verdict (`ok: false`, completed command with non-zero `exit_code`)**:
  - Emitted when `run`, `analyze`, or `probe` finishes without raising an exception while recommending a non-zero exit code (such as `exit_code: 7` with `reason_code: "inconclusive_quota_censored"`, `exit_code: 6` with `reason_code: "judge_evaluation_failed"`, or `exit_code: 2` with `reason_code: "probe_failed"`): carries `ok: false`, `mutations` (`"campaign_dir"` or `"none"`), and `data`.
- **Error / Guard Failure (`ok: false`, raised `HarnessEvalError` or usage error)**:
  - `exit_code`: normative non-zero code (`2`..`8`)
  - `reason_code`: machine-readable reason (`cli_usage_error`, `schema_validation_failed`, `api_keys_not_allowed`, `metered_env_in_subscription_mode`, `inconclusive_quota_censored`, etc.)
  - `mutations`: `"none"`
  - `error`: diagnostic message
  - `details`: structured context without secret values (present on `HarnessEvalError`)

## Paired `ABBA` Execution Semantics

1. Each block pairs baseline arm `A` against treatment arm `B` (or round-robin `ABBA` pairs for multi-arm protocols) on identical task fixtures and seeds.
2. Intention-To-Treat (`ITT`) scoring retains every scheduled trial in the denominator; crashes, timeouts, and verifier failures score `0.0` rather than being dropped.
3. Sensitivity output separates `cassette_miss` infrastructure failures from model task failures.
4. Any rate-limit or subscription quota exhaustion (`HTTP 429` / `quota_exhausted`) invalidates the **entire paired block** so time-of-day quota drift never biases one arm. When `> 20%` of blocks are quota-censored, the campaign exits `7` (`EXIT_INCONCLUSIVE_QUOTA`).

## Execution Modes (`headless`, `ntm`, `herdr`, `cao`)

- `headless`: Direct subprocess execution through the single-exec trampoline (`shim-exec.json` `O_CREAT|O_EXCL`).
- `ntm`: Standalone per-trial `tmux` server (`TMUX_TMPDIR=<trial>/tmux`, `-f <trial>/tmux.conf` with `rc-free-bash`) via `src/artagon_harness_eval/multiplexers/ntm.py`.
- `herdr`: Isolated pane execution with `pane-home` (`ZDOTDIR` `unsetopt GLOBAL_RCS` and `--no-brief`) via `scripts/herdr-swarm.sh`.
- `cao`: Ephemeral bearer-authenticated `cao-server` on `127.0.0.1:0` so any operator `cao-server` on `127.0.0.1:9889` remains untouched.
