import re

ALLOWED = {
    "dbw_agentops.gold.fact_agent_calls",
    "dbw_agentops.gold.agent_daily_metrics",
    "dbw_agentops.gold.agent_anomalies",
    "dbw_agentops.gold.dim_model_pricing",
}

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|merge|truncate|grant|revoke|copy|optimize|vacuum|call|set)\b", re.I)

# Words that end a FROM clause at the same nesting level.
FROM_CLAUSE_END = {
    "where", "group", "order", "limit", "having", "union", "intersect",
    "except", "window", "qualify", "lateral", "pivot", "unpivot", "tablesample",
}


def _has_comma_join(sql):
    """True if a comma separates table references in a FROM clause.

    A comma join (FROM allowed_table, other_table) lets a second table slip past
    the allowlist, because only the first name after FROM is captured by a
    simple regex. Explicit JOIN syntax is required instead.
    """
    s = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    s = re.sub(r"'(?:[^']|'')*'", "''", s)
    depth = 0
    open_from = []  # nesting depths that currently sit inside a FROM clause
    for m in re.finditer(r"\(|\)|,|\w+", s):
        tok = m.group().lower()
        if tok == "(":
            depth += 1
        elif tok == ")":
            while open_from and open_from[-1] >= depth:
                open_from.pop()
            depth -= 1
        elif tok == ",":
            if open_from and open_from[-1] == depth:
                return True
        elif tok == "from":
            open_from.append(depth)
        elif tok in FROM_CLAUSE_END:
            if open_from and open_from[-1] == depth:
                open_from.pop()
    return False


def validate_sql(sql):
    sql = sql.replace("```sql", "").replace("```", "").strip().rstrip(";").strip()
    sql = re.sub(r"--.*", "", sql).strip()
    if ";" in sql:
        raise ValueError("multiple statements are not allowed")
    if not re.match(r"^(select|with)\b", sql, re.I):
        raise ValueError("only SELECT queries are allowed")
    if FORBIDDEN.search(sql):
        raise ValueError("query contains a forbidden keyword")
    if _has_comma_join(sql):
        raise ValueError("comma joins are not allowed; use an explicit JOIN")
    ctes = {c.lower() for c in re.findall(r"\b(\w+)\s+as\s*\(", sql, re.I)}
    refs = [r.replace("`", "").lower() for r in re.findall(r"\b(?:from|join)\s+([\w\.`]+)", sql, re.I)]
    bad = [r for r in refs if r not in ALLOWED and r not in ctes]
    if bad:
        raise ValueError(f"table not allowed: {bad}")
    if not re.search(r"\blimit\s+\d+", sql, re.I):
        sql += " LIMIT 100"
    return sql
