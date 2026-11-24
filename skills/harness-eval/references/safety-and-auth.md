# Safety, Billing Guard, and Isolation Reference (`harness-eval`)

## Dual Authentication Modes (`auth_mode`)

| Mode | Flag Gate | Credential Delivery | Scrubbed State |
| --- | --- | --- | --- |
| `subscription` (default) | None | Isolated harness OAuth session (`persisted_eval_config_dir`, `CLAUDE_EVAL_OAUTH_TOKEN`, Codex `chatgpt`, Agy UID `secd` / read-only `xdg-dbus-proxy`, Copilot `account_id` with `max_ai_credits >= 30`) | All `METERED_BILLING_ENV_VARS` (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `COPILOT_PROVIDER_*`, Bedrock/Vertex/Foundry toggles) |
| `api_key` (opt-in) | `--allow-api-keys` + finite `max_cost_usd` or `max_tokens` | Mode `0400` `<trial>/secret/api_key` file read by the trampoline and unlinked in `finally:` | All subscription OAuth variables, `KEYCHAIN_DISABLE=1`, `DBUS_SESSION_BUS_ADDRESS=""` |

## Keyring Store Separation

- **macOS**: Keep metered API keys in a separate locked `.keychain-db` so subject processes running under subscription auth cannot read API keys from the default unlocked login keychain.
- **Linux**: Keep metered API keys in `pass` or a locked Secret Service collection, and route `agy` subscription reads through the read-only `xdg-dbus-proxy` socket (`/tmp/art-dbus-<rand>/bus`, `< 100` bytes).
- If store separation is unverified on bare host runs, preflight stamps `billing_guard: "env_only"` and scored shell trials require an OS container.

## Workspace & Observer Isolation

- Every trial executes inside a fresh `0700` directory under `/var/tmp/art-eval-<uid>` with ancestor scanning to `/` so parent `CLAUDE.md`, `AGENTS.md`, `.claude`, `.codex`, `.gemini`, or `.copilot` files never leak into subject context.
- Fixture repositories have ambient instruction and hook directories quarantined before subject launch unless explicitly declared by the arm.
- `OPERATOR_ONLY_SKILL_NAMES` (`harness-eval`, `harness-eval-author`, `harness-eval-trace`) are stripped from subject skill staging unless the arm explicitly names them under test.
