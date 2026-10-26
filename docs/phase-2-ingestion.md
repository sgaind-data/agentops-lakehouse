# Phase 2: Batch ingestion with Azure Data Factory (ELT)

## What was built

| Item | Name | Purpose |
|---|---|---|
| Data generator | `agent/generate_traces.py` | Simulates the upstream system: 7 daily JSONL trace files and a model pricing CSV |
| Source container | `landing` | Stand-in for an external source system dropping files (`traces/`, `pricing/`) |
| Data Factory | `adf-agentops-2026` | Orchestrates the batch copy (the E and L of ELT) |
| Linked service | `ls_adls_agentops` | Connection to the data lake using the factory's system-assigned managed identity, no keys |
| Dataset | `ds_adls_binary` | One parameterized Binary dataset (`container`, `folder`) reused for source and sink |
| Pipeline | `pl_ingest_landing_to_bronze` | Copies a folder from `landing` into `bronze/raw/<sourceFolder>` unchanged |
| Trigger | `tr_daily_traces` | Daily schedule at 2 AM Central for `traces`; created and published but left stopped to save credit |

## Design decisions and why

- **ELT, not ETL:** files are copied untouched into bronze. All cleaning happens later in Databricks (silver), so bronze stays a faithful record for replay and audit.
- **Binary copy:** the copy does not parse contents, so schema changes (the `region` field appears mid-period) and bad records cannot break ingestion.
- **Managed identity:** the factory gets the Storage Blob Data Contributor role on the storage account. No storage key exists to leak or rotate, and the role is least-privilege.
- **Parameterization:** one dataset and one pipeline serve both folders. `sourceFolder` is a pipeline parameter, passed by the trigger.
- **Idempotent loads:** rerunning copies the same files to the same paths, so repeats produce the same result.
- **Schedule trigger, stopped:** a schedule is the simplest recurring option. Tumbling windows would suit backfills and event triggers would suit load-on-arrival; neither is needed here.
- **JSON in Git:** pipeline, dataset, linked service and trigger definitions are stored under `adf/`.

## Verified results

- Debug runs for `traces` and `pricing` succeeded.
- `bronze/raw/traces` holds 7 files and `bronze/raw/pricing` holds 1 file.

## Known limitations

- The factory is not yet connected to Git, so the JSON in `adf/` is exported by hand.
- One trigger passes one `sourceFolder`; a ForEach in a parent pipeline would cover both folders.

## Next: Phase 3

Databricks single-node cluster, Auto Loader into bronze Delta tables, then silver and gold transformations with data quality checks.