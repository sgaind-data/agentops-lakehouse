import re

ALLOWED = {
    "dbw_agentops.gold.fact_agent_calls",
    "dbw_agentops.gold.agent_daily_metrics",
    "dbw_agentops.gold.agent_anomalies",
    "dbw_agentops.gold.dim_model_pricing",
}

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|merge|truncate|grant|revoke|copy|optimize|vacuum|call|set)\b", re.I)


def validate_sql(sql):
    sql = sql.replace("```sql", "").replace("```", "").strip().rstrip(";").strip()
    sql = re.sub(r"--.*", "", sql).strip()
    if ";" in sql:
        raise ValueError("multiple statements are not allowed")
    if not re.match(r"^(select|with)\b", sql, re.I):
        raise ValueError("only SELECT queries are allowed")
    if FORBIDDEN.search(sql):
        raise ValueError("query contains a forbidden keyword")
    ctes = {c.lower() for c in re.findall(r"\b(\w+)\s+as\s*\(", sql, re.I)}
    refs = [r.replace("`", "").lower() for r in re.findall(r"\b(?:from|join)\s+([\w\.`]+)", sql, re.I)]
    bad = [r for r in refs if r not in ALLOWED and r not in ctes]
    if bad:
        raise ValueError(f"table not allowed: {bad}")
    if not re.search(r"\blimit\s+\d+", sql, re.I):
        sql += " LIMIT 100"
    return sql