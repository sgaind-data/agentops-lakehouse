-- Datasets behind the AgentOps Lakehouse dashboard (Databricks AI/BI).
-- Each query is one dataset; the charts are built on top of them.

-- daily_by_agent: cost and prompt size per agent per day (cost and tokens charts)
SELECT event_date,
       agent_name,
       CAST(SUM(cost_usd) AS DOUBLE) AS cost_usd,
       COUNT(*) AS calls,
       ROUND(AVG(prompt_tokens), 0) AS avg_prompt_tokens,
       ROUND(AVG(latency_ms), 0) AS avg_latency_ms
FROM dbw_agentops.gold.fact_agent_calls
WHERE event_date < current_date()
GROUP BY event_date, agent_name
ORDER BY event_date;

-- flagged_anomalies: agent-days flagged by the z-score baseline or Isolation Forest
SELECT event_date,
       agent_name,
       ROUND(max_abs_z, 2) AS max_abs_z,
       ROUND(if_score, 3) AS if_score,
       stat_anomaly,
       if_anomaly
FROM dbw_agentops.gold.agent_anomalies
WHERE stat_anomaly = true OR if_anomaly = true
ORDER BY event_date DESC, agent_name;

-- judge_quality: average LLM-judge score per rubric dimension
SELECT 'relevance' AS dimension, ROUND(AVG(relevance), 2) AS avg_score FROM dbw_agentops.gold.agent_judge_scores
UNION ALL
SELECT 'faithfulness', ROUND(AVG(faithfulness), 2) FROM dbw_agentops.gold.agent_judge_scores
UNION ALL
SELECT 'clarity', ROUND(AVG(clarity), 2) FROM dbw_agentops.gold.agent_judge_scores;
