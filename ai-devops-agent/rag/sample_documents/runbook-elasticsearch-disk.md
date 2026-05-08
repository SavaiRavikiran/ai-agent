# Elasticsearch High Disk Usage

**Component:** Elasticsearch (logging/monitoring)  
**Doc type:** Runbook

## Symptoms

- Elasticsearch cluster health yellow/red due to disk space
- Indices read-only or allocation failures

## ILM policy check

1. List ILM policies: `GET _ilm/policy`
2. Ensure hot phase has `max_primary_shard_size` or rollover by age/size.
3. Ensure warm/delete phases delete or shrink old indices.

## Index cleanup

1. List indices by size: `GET _cat/indices?v&s=store.size:desc`
2. Delete old closed indices (e.g. filebeat-* older than 30 days) after confirming with retention policy:
   - `DELETE filebeat-7.17.0-2024.01.01` (example)
3. Use Curator or ILM delete phase for automation.

## Curator steps (if installed)

- Run curator with a delete action for indices older than N days.
- Ensure no critical indices are in the delete pattern.

## Verification

- `GET _cluster/health`
- `GET _cat/allocation?v`
- Check disk space on ES nodes.
