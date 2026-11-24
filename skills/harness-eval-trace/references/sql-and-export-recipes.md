# DuckDB SQL and Trace Export Recipes (`harness-eval-trace`)

## 1. Arm-Level ITT Pass Rate, Latency, and Token Summary

```sql
SELECT
  arm_id,
  harness,
  auth_mode,
  COUNT(*) AS trials,
  AVG(CASE WHEN verified_success THEN 1.0 ELSE 0.0 END) AS itt_pass_rate,
  AVG(duration_ms) AS mean_duration_ms,
  SUM(input_tokens) AS total_input_tokens,
  SUM(cache_read_tokens) AS total_cache_read_tokens,
  SUM(output_tokens) AS total_output_tokens,
  SUM(mcp_cassette_miss_count) AS cassette_misses
FROM trials
GROUP BY arm_id, harness, auth_mode
ORDER BY arm_id
```

## 2. Tool Error Hotspots Across Harnesses

```sql
SELECT
  t.arm_id,
  t.harness,
  c.tool_name,
  COUNT(*) AS calls,
  SUM(CASE WHEN c.status = 'error' THEN 1 ELSE 0 END) AS errors,
  AVG(c.duration_ms) AS avg_ms
FROM tool_calls AS c
JOIN trials AS t ON t.trial_id = c.trial_id
GROUP BY t.arm_id, t.harness, c.tool_name
ORDER BY errors DESC, calls DESC
```

## 3. Detect `Bash` Workspace Edits Not Attributed to File-Edit Tools

```sql
SELECT
  d.trial_id,
  t.arm_id,
  d.rel_path,
  d.change_kind
FROM file_diffs AS d
JOIN trials AS t ON t.trial_id = d.trial_id
WHERE NOT EXISTS (
  SELECT 1
  FROM tool_calls AS c
  WHERE c.trial_id = d.trial_id
    AND c.tool_name IN ('Edit', 'Write', 'MultiEdit', 'apply_patch', 'edit_file', 'write_file')
)
ORDER BY d.trial_id, d.rel_path
```

## 4. Inspect Unmatched MCP Cassette Requests (`cassette_miss`)

```sql
SELECT
  trial_id,
  server_name,
  tool_name,
  normalized_jcs_sha256,
  COUNT(*) AS misses
FROM mcp_calls
WHERE cassette_miss
GROUP BY trial_id, server_name, tool_name, normalized_jcs_sha256
ORDER BY misses DESC
```

## 5. Export Waterfalls to Arize Phoenix or MLflow 3

```bash
# Write OTLP/HTTP JSON payload for offline archive or inspection
python3 scripts/harness-eval.py --output json trace-export \
  --campaign /tmp/campaign-01 \
  --format otlp-json \
  --out /tmp/campaign-01/exports/otlp.json

# Export and POST to local Arize Phoenix (default collector port 6006)
python3 scripts/harness-eval.py --output json trace-export \
  --campaign /tmp/campaign-01 \
  --format phoenix \
  --out /tmp/campaign-01/exports/phoenix.json \
  --endpoint http://127.0.0.1:6006/v1/traces

# Export MLflow 3 GenAI span bundle
python3 scripts/harness-eval.py --output json trace-export \
  --campaign /tmp/campaign-01 \
  --format mlflow \
  --out /tmp/campaign-01/exports/mlflow-traces.json
```
