# Phase 6: Anomaly detection, agent and LLM-as-judge

## 6a. Anomaly detection (MLflow)
- Features per agent-day (28 rows): calls, avg prompt tokens, cost per call, avg latency, error rate.
- Baseline: robust z-score (median and MAD, per agent), flagged when any score exceeds 3.5.
- Model: Isolation Forest on the per-agent robust z-scores (200 trees, contamination 0.04).
- Evaluated against the planted spike (support-bot, Oct 24: prompt tokens 2,137 vs about 900 normally).

| Detector | Precision | Recall | Rows flagged |
|---|---|---|---|
| Robust z-score baseline | 0.25 | 1.00 | 4 |
| Isolation Forest | 0.50 | 1.00 | 2 |

- Both runs, with parameters and metrics, are tracked in MLflow. The model is registered in Unity Catalog as `dbw_agentops.gold.agent_anomaly_iforest`.
- Scores are saved to `gold.agent_anomalies` for dashboards and the agent.
- Limitation: 28 rows and one known anomaly demonstrate the method and the evaluation habit, not general superiority.

## 6b. "Ask the Lakehouse" agent
- LLM: `gpt-oss-120b`, hosted by Databricks and reached through Unity Gateway. No external key, because the Azure OpenAI trial quota is zero.
- Flow: schema context from the real gold tables, then SQL generation, then guardrails, then execution, then a plain-English answer.
- Guardrails are enforced in code, not by the model: a single SELECT only, no write keywords, an allowlist of four gold tables, and an automatic row limit. A "delete all rows" request was blocked.
- Every question, query and answer is logged to `gold.agent_qa_log`, so the platform monitors the agent it powers.

## 6c. LLM-as-judge
- A second pass scores each logged answer for relevance, faithfulness and clarity (1 to 5). The judge re-runs the SQL and sees the real rows, so it checks facts, not just wording.
- Judge v1: 91% pass, but it missed two of three failures I had labelled by hand (82% agreement).
- Judge v2 (rubric tightened: placeholder SQL scores 1, ignored filters capped at 3): 82% pass, 91% agreement with my labels.
- Agent fixes driven by the judge: refuse out-of-scope questions, always apply named filters, return the top 5 instead of LIMIT 1, aggregate across models before comparing, use units, never claim "the only one" from partial rows.
- Agent v2 re-judged: 89% pass (8 of 9). The CEO question is now refused and passes; the error-rate answer is fixed; the p95 question is still flagged (faithfulness 3).
- All runs are in MLflow.

## Limitations I would state in an interview
- The judge is the same model that wrote the answers (self-preference bias). In production, use a different model family.
- The rubric was tuned on the same 11 examples, so agreement is optimistic. Keep a held-out labelled set.
- One human rater (me). Real evaluation needs several.
- The p95 granularity problem is still not fully solved.

## Problems I hit and fixed
- The Serving page showed no foundation model endpoints. They had moved to Unity Gateway, where `gpt-oss-120b` was available.
- Judge v1 was too lenient. It accepted a made-up answer because the answer matched the made-up rows. Fixed by telling it to inspect the SQL first.