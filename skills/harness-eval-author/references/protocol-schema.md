# Protocol Schema Reference (`harness-eval-protocol/v1`)

All protocol manifests validate against `<repo-or-plugin>/schemas/harness-eval/protocol.schema.json` (JSON Schema Draft 2020-12, `additionalProperties: false`).

## Top-Level Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `schema_version` | `"harness-eval-protocol/v1"` | Yes | Exact protocol schema identifier. |
| `campaign_id` | `string` (`^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$`) | Yes | Campaign identifier slug. |
| `seed` | `integer >= 0` | Yes | Deterministic RNG seed for `ABBA` block ordering, bootstrap CIs, and blind-judge shuffling. |
| `repetitions` | `integer >= 1` | No (`1`) | Number of paired `ABBA` block repetitions per task. |
| `execution_mode` | `"headless" \| "ntm" \| "herdr" \| "cao"` | No (`"headless"`) | Tier-1 (`headless`) or Tier-2 multiplexer backend. |
| `pin_mode` | `"nix" \| "host"` | No (`"nix"`) | Offline Nix closure pin (default) or bare-host pin (requires `--allow-host-pin`). |
| `cassette_miss_threshold` | `number` (`0.0`..`1.0`) | No (`0.0`) | Maximum tolerated `cassette_miss` fraction before exit `6`. |
| `arms` | `array[Arm]` (`minItems: 1`) | Yes | Frozen 4-tuple arm definitions (`arms[0]` is baseline control `A` unless overridden). |
| `tasks` | `array[Task]` (`minItems: 1`) | Yes | Task fixtures, prompts, and deterministic `verifier_cmd` definitions. |
| `budget` | `Budget` | Yes | `max_wall_seconds` plus optional `max_calls`, `max_tokens`, `max_cost_usd`, `max_ai_credits`, `max_output_bytes`. |
| `judge` | `Judge` | No | Optional vendor-blind and billing-blind LLM judge specification. |

## Arm 4-Tuple Structure

```json
{
  "arm_id": "agy-treatment-skill",
  "harness": "agy",
  "model": "gemini-4-carbon-high",
  "effort": "high",
  "auth_mode": "subscription",
  "harness_config": {
    "extra_args": [],
    "settings": {}
  },
  "mcp_servers": [
    {
      "name": "canary-docs",
      "mode": "cassette_replay",
      "cassette_path": "examples/cassettes/canary-docs.json"
    }
  ],
  "skills": [
    "plugins/artagon-shell/skills/shell-defensive"
  ],
  "system_prompt": {
    "mode": "append",
    "text": "Solve the task in the workspace and run the verifier before finishing."
  }
}
```
