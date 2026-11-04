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