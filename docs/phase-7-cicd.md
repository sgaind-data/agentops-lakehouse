# Phase 7: CI/CD and data contracts

## What I built
- **Databricks Asset Bundle** (`databricks.yml`): the pipeline as code. One job, `agentops_daily_pipeline`, with three chained tasks (`bronze_ingest`, `silver_traces`, `gold_metrics`), a single-node job cluster that starts for the run and terminates afterward, and a 06:30 America/Chicago schedule defined as code and kept paused. The `dev` target uses development mode, which prefixes the job name with my username so it cannot collide with other jobs.
- **Guardrail tests** (`agent/guardrails.py`, `tests/test_guardrails.py`): the agent's SQL contract as code. 8 tests cover SELECT-only, one statement, the table allowlist, forbidden keywords (including a write hidden behind a CTE) and the automatic row limit.
- **GitHub Actions** (`.github/workflows/ci.yml`):
  - `test-and-validate` runs on every pull request and every push to `main`: the 8 tests, then `databricks bundle validate`.
  - `deploy` runs only on a push to `main` and only after the first job passes: `databricks bundle deploy`.

## Results
- First pull request run: green in 12 seconds. The deploy job showed as skipped, which is intended, so unreviewed code can never deploy.
- Merge to `main`: both jobs green, deploy in 14 seconds. The log read `0 created, 0 changed, 1 unchanged`, an idempotent deployment.
- `databricks bundle run`: the deployed pipeline finished with SUCCESS in about 10 minutes, including cluster start-up.

## Why these choices
- **Bundle instead of a hand-built job:** the click-built job was not versioned. Now the repo can rebuild the pipeline.
- **Job cluster:** costs less and describes the compute in code. It uses the same machine size as my interactive cluster to fit the 4-core trial quota.
- **Deploy only from `main`:** review happens before deployment.
- **Tests as the contract:** a rule that is not tested is only a wish. A change that breaks a guardrail fails the pull request.
- **Secrets by name:** the workflow references `DATABRICKS_HOST` and `DATABRICKS_TOKEN` stored as GitHub secrets. No credential is in the repo.

## Known limitations
- Authentication uses a short-lived personal access token (7 days). In production I would use a service principal with OIDC federation, so no long-lived token exists.
- Only a `dev` target exists. A real setup would add `staging` and `prod` targets with approval gates.
- The notebook still holds its own copy of the guardrail code. A next step is for the notebook to import the tested module, giving one source of truth.
- The streaming task is not in the bundle, because Event Hubs was deleted to stop hourly billing.
- Silver data-quality rules live in a notebook and are not unit tested yet.

## Problems I hit and fixed
- Homebrew could not install the Databricks CLI (Command Line Tools too old). Used the official prebuilt installer with sudo instead.
- The Runs list in the UI showed nothing for a few minutes after `bundle run`. The direct Run URL printed by the CLI showed the live run.