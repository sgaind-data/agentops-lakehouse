# Phase 8: Dashboard, write-up and teardown

## Goal
Turn the pipeline's gold tables into something a person can read in 30 seconds, document the project, and shut down paid resources.

## What was built
A Databricks AI/BI dashboard, **AgentOps Lakehouse**, with four views, each backed by its own SQL dataset on the gold layer:

| View | Dataset | What it shows |
|---|---|---|
| Daily cost by agent (USD) | `daily_by_agent` | support-bot cost jumps to about 1.15 on 2026-10-24 while other agents stay near 0.7 to 0.8 |
| Average prompt tokens by agent | `daily_by_agent` | root cause: support-bot prompt size rises from about 900 to over 2,100 tokens on the same day |
| Flagged anomalies table | `flagged_anomalies` | agent-days flagged by the z-score and by Isolation Forest, side by side |
| Agent answer quality | `judge_quality` | average LLM-judge score per rubric dimension (relevance, faithfulness, clarity); faithfulness is lowest |

The dashboard reads the story in order: what happened (cost), why (tokens), what the ML model caught (anomalies), and whether the agent's answers are any good (quality).

## Why these tools
- **AI/BI dashboard:** native to Databricks and reads Unity Catalog tables directly, so no data is copied to a separate BI tool.
- **Serverless SQL warehouse:** runs on Databricks-managed compute outside the free-trial core quota and bills only while running.
- **Genie (AI assistant):** charts were created from precise plain-English prompts, then checked against known results (the planted spike). Vague prompts produce generic charts; specific prompts name the dataset, chart type, axes and grouping. The AI draws the chart, but the author must verify it.
- **Publish with shared data permission:** viewers see results using the publisher's credentials and a shared cache, so they need no table access and the warehouse runs less often.

## Decisions and caveats
- The last day of data is partial, so the support-bot line dips on 2026-10-25. Left visible rather than hidden.
- The quality chart averages all judged rows in `gold.agent_judge_scores`, which may include more than one judge run. A stricter version would filter to the latest rubric version.
- The dashboard stays private; only a screenshot is committed to the repo.

## Teardown
Paid or trial-limited resources are deleted after the screenshots are captured: the Databricks workspace first, then the resource group, then the access token and GitHub secrets. Event Hubs was already deleted after Phase 4.

## Interview talking points
- A dashboard is a story, not a chart collection: cost, cause, detection, quality.
- Using Genie shows prompt precision plus verification against ground truth.
- Every number on the dashboard traces back to a gold table built by a tested, deployed pipeline.
