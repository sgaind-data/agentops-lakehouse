# Phase 4: Streaming with Event Hubs

## What I built
- Azure Event Hubs (Standard tier) namespace with an event hub `agent-traces` (2 partitions).
- A producer notebook that emits agent traces shaped like the batch data, with `event_time` set to now, over the Kafka protocol.
- A Structured Streaming notebook that reads the event hub, parses the JSON into columns and writes a Delta table `bronze.agent_traces_stream`, keeping the Kafka partition and offset.
- Silver now combines the batch bronze table and the stream bronze table, with the same dedupe, quarantine and MERGE rules.
- The Workflow now has two parallel bronze tasks (`bronze_ingest`, `stream_ingest`) feeding `silver_traces`, then `gold_metrics`.

## Result
- Sent 20 events, then 30 more. The stream table held 20, then 50 rows, not 70, which proves the checkpoint only reads new events.
- Silver 13,839 and gold fact 13,839 with 0 null costs after the merge.

## Why these choices
- **Kafka protocol on Event Hubs:** Databricks reads it with no extra library, and Standard tier supports it.
- **Secret in Key Vault via a secret scope:** the connection string never appears in a notebook or in Git. This needed the Key Vault Secrets User role for the AzureDatabricks service, because the vault uses RBAC.
- **availableNow trigger:** processes everything waiting, then stops, which is cheap on a trial. Always-on streaming is a one-line change to `processingTime`.
- **Separate bronze tables, converge in silver:** raw shapes differ, so each source keeps its own bronze table. Silver is where they become one trusted table.
- **Event Hubs deleted after the phase:** it is the only hourly-billed resource, and the Delta table keeps the data.

## Event Hubs vs Kafka
Event Hubs is a managed Azure service that also speaks the Kafka protocol. Kafka needs you to run the cluster. Event Hubs trades some Kafka features for zero operations.

## Problems I hit and fixed
- `PERMISSION_DENIED` reading the secret: the Key Vault used RBAC and Databricks had no role. Fixed by assigning Key Vault Secrets User to the AzureDatabricks application.