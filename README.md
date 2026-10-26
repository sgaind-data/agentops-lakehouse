# AgentOps Lakehouse

> Observability, FinOps and quality monitoring for AI agents, built end to end on Azure and Databricks.

**Status:** Day 1 of 25. Work in progress, updated as each phase ships.

## The problem

Teams are shipping AI agents faster than they can answer three questions:

1. **What is this agent costing us?** (per agent, per user, per query type, per day)
2. **Is it behaving?** (latency, errors, tool-call failures, answer quality)
3. **Can we trust the data pipeline that tells us?** (data contracts, quality checks, self-diagnosing failures)

AgentOps Lakehouse answers these with a medallion lakehouse that ingests agent traces in batch and streaming.
The twist: the platform monitors a real "Ask the Lakehouse" agent that it also powers, so the project analyzes itself.

## Architecture

```
Agent traces (stream)        Pricing + usage files (batch)
        |                               |
   Event Hubs                    Azure Data Factory (ELT)
        |                               |
        +---------------+---------------+
                        v
        ADLS Gen2:  bronze  ->  silver  ->  gold
                        |
        Databricks: Auto Loader, Structured Streaming,
                    Lakeflow pipelines, Workflows, Unity Catalog
                        |
        +---------------+-------------------+
        v               v                   v
   FinOps dashboard   MLflow anomaly     LLM-as-judge quality scores
                      detection          + "pipeline doctor" agent

   Key Vault - Managed Identity - Azure Monitor - GitHub Actions CI/CD
```

## Tech stack

| Layer | Tools |
|---|---|
| Storage | Azure Data Lake Storage Gen2, Delta Lake |
| Ingestion | Azure Data Factory (batch ELT), Event Hubs (streaming) |
| Processing | Azure Databricks, PySpark, Structured Streaming, Lakeflow pipelines |
| Governance | Unity Catalog, data contracts, quality expectations |
| ML / AI | MLflow, LLM-as-judge evaluation, retrieval-augmented agent |
| Security | Key Vault, Managed Identity, RBAC |
| DevOps | GitHub, GitHub Actions, Databricks Asset Bundles, IaC |

## Repo layout

```
infra/       Infrastructure as code (resource group, storage, Key Vault, Event Hubs)
adf/         Data Factory pipelines and datasets (exported JSON)
databricks/  Notebooks, pipelines, workflows, asset bundle config
ml/          Anomaly detection and evaluation code
agent/       The "Ask the Lakehouse" agent and trace emitter
docs/        Diagrams, screenshots, design notes
tests/       Unit and data-quality tests
```

## Progress

- [ ] Phase 1: Foundation (resource group, budget alerts, ADLS, Key Vault)
- [ ] Phase 2: Batch ingestion with ADF (ELT)
- [ ] Phase 3: Databricks medallion layers
- [ ] Phase 4: Streaming with Event Hubs
- [ ] Phase 5: Orchestration with Databricks Workflows
- [ ] Phase 6: Agent, anomaly detection and LLM-as-judge
- [ ] Phase 7: CI/CD and data contracts
- [ ] Phase 8: Write-up, dashboard and teardown

## Cost discipline

Built within a 25-day Azure free trial ($200 credit, spending limit on). Job clusters auto-terminate,
the streaming components are created only for their phase, and the whole resource group is deleted at the end.

## Author

Built by *your name here*. Follow the build log on LinkedIn: *link here*.
