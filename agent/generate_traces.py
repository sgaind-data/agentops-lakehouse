"""
Synthetic AI-agent telemetry generator for AgentOps Lakehouse.

Creates two kinds of source data:
  1. Agent traces   -> data/raw/traces/agent_traces_YYYY-MM-DD.jsonl  (one JSON object per LLM call)
  2. Model pricing  -> data/raw/pricing/model_pricing.csv             (reference data, includes a price change)

The data is deliberately imperfect so the pipeline has real work to do:
  - duplicate events                (-> deduplication in silver)
  - missing user_id / model values  (-> data quality checks and quarantine)
  - late-arriving events            (-> watermarking, ingest_time vs event_time)
  - a new field ("region") that appears halfway through the period (-> schema evolution)
  - one cost/latency spike on one agent (-> anomaly detection later)
  - a mid-period price change       (-> slowly changing dimension, SCD Type 2)

All prices and model names are illustrative, not real vendor prices.

Usage (from the repo root):
    python agent/generate_traces.py --days 7 --events-per-day 2000
"""

import argparse
import csv
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

AGENTS = ["sql-assistant", "support-bot", "doc-summarizer", "code-reviewer"]
QUERY_TYPES = ["lookup", "aggregation", "join", "summary", "chat"]
ERROR_TYPES = ["rate_limited", "tool_failure", "invalid_sql", "context_too_long"]
REGIONS = ["us-east", "us-central", "eu-west"]

# Illustrative USD prices per 1 million tokens, and a typical base latency in ms.
MODELS = {
    "small-model-a": {"input": 0.15, "output": 0.60, "latency": 700, "weight": 0.55},
    "medium-model-b": {"input": 0.80, "output": 3.20, "latency": 1200, "weight": 0.30},
    "large-model-c": {"input": 3.00, "output": 12.00, "latency": 2400, "weight": 0.15},
}


def make_event(day, spike_day, add_region):
    """Build one agent trace event for a given day."""
    agent = random.choice(AGENTS)
    model = random.choices(list(MODELS), weights=[m["weight"] for m in MODELS.values()])[0]
    spec = MODELS[model]

    start_of_day = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    event_time = start_of_day + timedelta(seconds=random.randint(0, 86399))

    prompt_tokens = max(20, int(random.gauss(900, 300)))
    completion_tokens = max(5, int(random.gauss(250, 100)))
    latency_ms = max(50, int(random.gauss(spec["latency"], spec["latency"] * 0.25)) + completion_tokens * 2)

    status = random.choices(["success", "error", "timeout"], weights=[96, 3, 1])[0]
    error_type = random.choice(ERROR_TYPES) if status == "error" else None
    if status == "timeout":
        latency_ms = 30000

    # Anomaly: a runaway prompt loop in one agent on one day.
    if spike_day and agent == "support-bot" and random.random() < 0.30:
        prompt_tokens *= 6
        latency_ms *= 4

    # Most events arrive within seconds; about 2% arrive hours late.
    if random.random() < 0.02:
        ingest_time = event_time + timedelta(hours=random.randint(2, 6))
    else:
        ingest_time = event_time + timedelta(seconds=random.randint(1, 5))

    event = {
        "trace_id": str(uuid.uuid4()),
        "event_time": event_time.isoformat(),
        "ingest_time": ingest_time.isoformat(),
        "agent_name": agent,
        "user_id": f"user_{random.randint(1, 200):03d}",
        "model": model,
        "query_type": random.choice(QUERY_TYPES),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "tool_calls": random.randint(0, 4),
        "latency_ms": latency_ms,
        "status": status,
        "error_type": error_type,
    }
    if add_region:  # schema drift: new field appears midway through the period
        event["region"] = random.choice(REGIONS)

    # Data quality defects
    if random.random() < 0.01:
        event["user_id"] = None
    if random.random() < 0.005:
        event["model"] = None
    return event


def write_traces(out_dir, days, events_per_day):
    traces_dir = out_dir / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).date()
    first_day = today - timedelta(days=days)
    spike_index = days - 2          # spike happens near the end of the period
    drift_index = days // 2         # "region" appears from the middle onwards

    total = 0
    for i in range(days):
        day = first_day + timedelta(days=i)
        events = [make_event(day, i == spike_index, i >= drift_index) for _ in range(events_per_day)]

        # About 1% duplicate events, as happens with at-least-once delivery.
        events += random.sample(events, k=max(1, events_per_day // 100))
        events.sort(key=lambda e: e["event_time"])

        path = traces_dir / f"agent_traces_{day.isoformat()}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")
        total += len(events)

    print(f"Wrote {days} trace files with {total} events to {traces_dir}")
    return first_day


def write_pricing(out_dir, first_day, days):
    pricing_dir = out_dir / "pricing"
    pricing_dir.mkdir(parents=True, exist_ok=True)

    old_start = first_day - timedelta(days=30)
    change_day = first_day + timedelta(days=days // 2)

    rows = []
    for model, spec in MODELS.items():
        if model == "small-model-a":
            # Price drop midway through the period -> two versions of the same model.
            rows.append([model, spec["input"] * 1.5, spec["output"] * 1.5, old_start.isoformat()])
            rows.append([model, spec["input"], spec["output"], change_day.isoformat()])
        else:
            rows.append([model, spec["input"], spec["output"], old_start.isoformat()])

    path = pricing_dir / "model_pricing.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["model", "input_usd_per_1m_tokens", "output_usd_per_1m_tokens", "effective_from"])
        writer.writerows(rows)
    print(f"Wrote pricing file with {len(rows)} rows to {path}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic agent telemetry.")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--events-per-day", type=int, default=2000)
    parser.add_argument("--out", type=Path, default=Path("data/raw"))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    first_day = write_traces(args.out, args.days, args.events_per_day)
    write_pricing(args.out, first_day, args.days)


if __name__ == "__main__":
    main()
