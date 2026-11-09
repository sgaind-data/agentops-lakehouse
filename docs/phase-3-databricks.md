# Phase 3: Databricks medallion layers

## What was built
- Azure Databricks workspace (Hybrid, Trial tier) with a single-node cluster that fits the 4-core trial quota.
- Unity Catalog: catalog `dbw_agentops` with `bronze`, `silver` and `gold` schemas, each with a managed location in ADLS Gen2.
- Access path: access connector (managed identity) -> storage credential -> external locations. No keys or passwords in code.
- Three pipeline notebooks in `databricks/notebooks/`.

## The pipeline
| Notebook | Layer | What it does |
|---|---|---|
| `01_bronze_ingest` | Bronze | Auto Loader loads new JSON trace files incrementally. A checkpoint tracks processed files, so reruns add nothing. Schema evolution picked up the new `region` column. Pricing CSV is loaded with an idempotent overwrite. |
| `02_silver_traces` | Silver | Types timestamps, dedupes by `trace_id` with a window function, checks data-contract rules, quarantines violations with the reason, and loads with `MERGE`. |
| `03_gold_metrics` | Gold | Builds an SCD Type 2 pricing dimension, a fact table using a point-in-time join, and daily metrics per agent and model. |

## Numbers (reconciled at every layer)
- Bronze: 14,140 rows (includes ~1% duplicates)
- Unique traces: 14,000
- Silver: 13,789 | Quarantine: 211 (missing user_id or model)
- Gold fact: 13,789 rows, 0 null costs

## Why these choices
- **Auto Loader over a plain read:** it tracks which files are processed, so loads are incremental and idempotent.
- **Quarantine instead of dropping:** bad rows stay visible and fixable, and nothing disappears silently.
- **MERGE in silver:** rerunning never creates duplicates.
- **SCD Type 2 pricing:** the small-model-a price drop mid-period means old calls must keep the old price. A plain join would misprice history.
- **DECIMAL for money:** floats drift, decimals do not.
- **One notebook per layer:** each becomes a task in the Phase 5 Workflow.

## Problems hit and fixed
- File events validation failed on the external location (optional feature). Used Force create; Auto Loader falls back to directory listing.
- `DELTA_METADATA_MISMATCH` when overwriting the quarantine table. Delta protects schemas by default, so I added `overwriteSchema` because the change was intentional.

## Planted anomaly for Phase 6
The support-bot agent spikes in prompt tokens, latency and cost on the second-to-last day. It is visible in `agent_daily_metrics` and is what anomaly detection will catch.