# Phase 1: Foundation

## What was built

| Resource | Name | Purpose |
|---|---|---|
| Resource group | `rg-agentops-dev` | Container for every project resource, deleted at the end to stop all costs |
| Budget | $150 with alerts at 50/75/90% | Early warning on spend, on top of the free trial spending limit |
| Storage account (ADLS Gen2) | `stagentops...` | Data lake with hierarchical namespace, Standard performance, LRS, Hot tier |
| Containers | `bronze`, `silver`, `gold` | Medallion architecture layers |
| Key Vault | `kv-agentops-2026` | Stores the LLM API key, RBAC permission model, soft delete on, purge protection off |

## Design decisions and why

- **Free trial, no upgrade:** the spending limit caps spend at the credit amount, so no real money can be charged.
- **Hierarchical namespace:** gives real folders, fast renames and folder-level permissions that Spark needs.
- **LRS redundancy:** cheapest option, enough for a learning project. Production would use ZRS or GRS.
- **Medallion layers:** bronze keeps raw data untouched for replay and audit, silver is cleaned and validated, gold is business-ready.
- **Key Vault with RBAC:** secrets are fetched at runtime and never stored in code or Git. Management-plane and data-plane permissions are separate, so a role assignment was needed to write secrets.
- **Purge protection off:** allows full teardown at the end of the project. Production would enable it.
- **Branch and pull request workflow:** `main` stays clean, and each phase merges through a PR.

## Security notes

- No keys, subscription IDs or secret values are stored in this repo.
- `.gitignore` excludes `.env`, key files and local config.

## Next: Phase 2

Batch ingestion with Azure Data Factory (ELT) and a synthetic agent-trace data generator.