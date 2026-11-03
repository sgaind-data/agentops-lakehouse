# Phase 5: Orchestration with Databricks Workflows

## What I built
A Databricks Workflow (job) `agentops_daily_pipeline` with three dependent tasks:

`bronze_ingest -> silver_traces -> gold_metrics`

Each task runs one notebook from `databricks/notebooks/`. A task starts only when the one before it succeeds, so bad data never flows downstream.

## Result
- Full run: 2m 36s on the existing single-node cluster.
- Rerun on already-loaded data changed nothing: silver 13,789, quarantine 211, fact 13,789, null costs 0. This proves the pipeline is idempotent.

## Why these choices
- **One task per layer:** a failure points to exactly one stage, and a single stage can be rerun alone.
- **Dependencies instead of one big notebook:** clearer lineage, retries per task, easier to monitor.
- **Existing cluster, not a job cluster:** the trial's 4-core quota allows only one cluster. In production I would use a job cluster that starts and stops per run, which costs less.
- **No schedule enabled:** the job supports a cron schedule, kept manual to protect trial credit. It will be defined as code in Phase 7.

## ADF vs Databricks Workflows
ADF moves files into the lake (landing to bronze). Workflows transforms data (bronze to silver to gold). They can be chained: ADF can call a Databricks job after its copy activity finishes.