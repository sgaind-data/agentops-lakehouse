import pytest
from agent.guardrails import validate_sql

T = "dbw_agentops.gold.fact_agent_calls"


def test_adds_default_limit():
    assert validate_sql(f"SELECT * FROM {T};").endswith("LIMIT 100")


def test_keeps_existing_limit():
    assert validate_sql(f"SELECT * FROM {T} LIMIT 5").upper().count("LIMIT") == 1


def test_table_names_are_case_insensitive():
    validate_sql("SELECT * FROM DBW_AGENTOPS.GOLD.FACT_AGENT_CALLS")


def test_allows_cte():
    validate_sql(f"WITH t AS (SELECT * FROM {T}) SELECT * FROM t")


def test_blocks_delete():
    with pytest.raises(ValueError):
        validate_sql(f"DELETE FROM {T}")


def test_blocks_multiple_statements():
    with pytest.raises(ValueError):
        validate_sql(f"SELECT * FROM {T}; DROP TABLE {T}")


def test_blocks_tables_outside_the_allowlist():
    with pytest.raises(ValueError):
        validate_sql("SELECT * FROM system.access.audit")


def test_blocks_write_hidden_behind_a_cte():
    with pytest.raises(ValueError):
        validate_sql(f"WITH x AS (SELECT 1) DELETE FROM {T}")

def test_blocks_comma_join_to_a_table_outside_the_allowlist():
    with pytest.raises(ValueError):
        validate_sql(f"SELECT * FROM {T}, system.access.audit")


def test_blocks_comma_join_with_aliases_and_newlines():
    with pytest.raises(ValueError):
        validate_sql(f"SELECT * FROM {T} a,\n system.information_schema.tables b")


def test_blocks_comma_join_after_a_subquery():
    with pytest.raises(ValueError):
        validate_sql(f"SELECT * FROM (SELECT * FROM {T}) x, system.access.audit y")


def test_commas_outside_from_clauses_are_fine():
    validate_sql(f"SELECT agent_name, SUM(cost_usd) FROM {T} GROUP BY agent_name, model ORDER BY 2 DESC")
    validate_sql(f"SELECT * FROM {T} WHERE agent_name IN ('a', 'b') AND latency_ms > 5")
    validate_sql(f"SELECT CAST(cost_usd AS DECIMAL(10, 2)) FROM {T}")
    validate_sql(f"WITH a AS (SELECT * FROM {T}), b AS (SELECT * FROM {T}) SELECT * FROM a JOIN b ON a.trace_id = b.trace_id")
