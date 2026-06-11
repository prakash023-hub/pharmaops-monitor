#!/usr/bin/env python3
"""
PharmaOps Watchdog — Auto-triggers multi-agent on new Splunk anomalies.

Simulates Splunk alert → webhook → agent pipeline.
Usage: python3 watchdog.py --once
       python3 watchdog.py --interval 60
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from config import REPORTS_DIR
from multi_agent import run_multi_agent
from splunk_mcp import detect_top_anomaly

STATE_FILE = REPORTS_DIR / "watchdog_state.json"


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_batch": None, "investigations": []}


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def check_and_investigate(log=print) -> bool:
    """Check for new anomaly; trigger multi-agent if batch changed."""
    anomaly = detect_top_anomaly()
    if not anomaly:
        log("[Watchdog] No anomalies.")
        return False

    state = _load_state()
    batch_id = anomaly["batch_id"]

    if batch_id == state.get("last_batch"):
        log(f"[Watchdog] No new anomalies (still {batch_id}).")
        return False

    log(f"[Watchdog] NEW ANOMALY: {batch_id} — triggering multi-agent pipeline...")
    report = run_multi_agent(log=log)
    if report:
        state["last_batch"] = batch_id
        state["investigations"].append({
            "batch_id": batch_id,
            "report_id": report["report_id"],
            "timestamp": datetime.now().isoformat(),
        })
        _save_state(state)
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="PharmaOps anomaly watchdog")
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    parser.add_argument("--interval", type=int, default=0, help="Poll interval in seconds")
    args = parser.parse_args()

    if args.once or args.interval == 0:
        check_and_investigate()
    else:
        print(f"[Watchdog] Polling every {args.interval}s — Ctrl+C to stop")
        while True:
            check_and_investigate()
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
