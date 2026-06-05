#!/usr/bin/env python3
"""
PharmaOps Autonomous GMP Investigator

Detects temperature anomalies via Splunk MCP, investigates root cause with
Gemini, and generates FDA-compliant deviation reports.

Usage:
  python3 pharma_agent.py --autonomous          # detect + investigate top anomaly
  python3 pharma_agent.py --batch BATCH-1011    # investigate specific batch
  python3 pharma_agent.py --demo                 # investigate top 2 anomalies
  python3 pharma_agent.py --open-report         # open HTML report in browser
"""

import argparse
import json
import os
import sys
from datetime import datetime

from google import genai

from config import GEMINI_MODEL, REPORTS_DIR, SPLUNK_INDEX
from generate_report_html import save_html_report
from splunk_mcp import detect_top_anomaly, search

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def _query_evidence(batch_id: str) -> dict:
    queries = {
        "temperature": (
            f"search index={SPLUNK_INDEX} source=temperature_logs.csv batch_id=\"{batch_id}\" "
            "| stats avg(temperature_C) as avg_temp max(temperature_C) as max_temp "
            "min(temperature_C) as min_temp count as readings by equipment_id"
        ),
        "deviations": (
            f"search index={SPLUNK_INDEX} source=temperature_logs.csv batch_id=\"{batch_id}\" status=DEVIATION "
            "| table timestamp temperature_C equipment_id status | head 10"
        ),
        "batch_qc": (
            f"search index={SPLUNK_INDEX} source=batch_summary.csv batch_id=\"{batch_id}\" "
            "| table batch_id product yield_pct deviation_count batch_status oee_score"
        ),
        "equipment_downtime": (
            f"search index={SPLUNK_INDEX} source=equipment_downtime.csv "
            "| stats sum(downtime_minutes) as total_downtime count as events by equipment_id "
            "| sort -total_downtime | head 5"
        ),
        "moisture": (
            f"search index={SPLUNK_INDEX} source=moisture_logs.csv batch_id=\"{batch_id}\" "
            "| stats avg(moisture_pct) as avg_moisture max(moisture_pct) as max_moisture "
            "count as deviation_count by equipment_id"
        ),
    }

    evidence = {}
    for name, spl in queries.items():
        print(f"  [MCP] Querying {name}...")
        result = search(spl)
        evidence[name] = {
            "source": result.get("source", "unknown"),
            "rows": result.get("rows", [])[:10],
        }
        if result.get("warning"):
            evidence[name]["warning"] = result["warning"]
    return evidence


def investigate_batch(
    batch_id: str,
    anomaly_type: str = "temperature_deviation",
    deviation_sigma: float = 2.5,
    deviation_count: int = 0,
    open_report: bool = False,
) -> dict:
    print(f"\n{'='*60}")
    print(f"  INVESTIGATING: {batch_id}")
    print(f"  Anomaly: {anomaly_type} | Severity: {deviation_sigma}σ")
    print(f"{'='*60}")

    print("\n[STEP 1/4] Gathering evidence from Splunk MCP...")
    evidence = _query_evidence(batch_id)

    print("\n[STEP 2/4] Reasoning with Gemini LLM...")
    prompt = f"""You are PharmaOps Agent, an autonomous GMP compliance investigator for pharmaceutical manufacturing.

ANOMALY DETECTED (autonomous detection):
- Batch ID: {batch_id}
- Anomaly Type: {anomaly_type}
- Deviation Severity: {deviation_sigma} sigma
- Deviation Events: {deviation_count}
- Investigation Time: {datetime.now().isoformat()}

EVIDENCE FROM SPLUNK MCP (live manufacturing data):
{json.dumps(evidence, indent=2)}

Based ONLY on the evidence above, provide a structured GMP deviation report:

1. ROOT CAUSE (evidence-based, cite specific temperature values and equipment IDs)
2. GMP IMPACT: Critical / Major / Minor (with justification)
3. CORRECTIVE ACTION (CAPA) — immediate containment + preventive actions
4. FINANCIAL IMPACT (INR lakhs range, e.g. 15-30 lakhs)
5. CONFIDENCE SCORE (e.g. 4.5/5 with brief reasoning)

Be specific. Reference actual batch IDs, equipment IDs, and numbers from the evidence."""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    analysis = response.text

    print("\n[STEP 3/4] Building structured report...")
    report = {
        "report_id": f"DEV-{batch_id}-{datetime.now().strftime('%Y%m%d%H%M')}",
        "batch_id": batch_id,
        "anomaly_type": anomaly_type,
        "deviation_sigma": deviation_sigma,
        "deviation_count": deviation_count,
        "timestamp": datetime.now().isoformat(),
        "evidence": evidence,
        "agent_analysis": analysis,
    }

    json_path = REPORTS_DIR / f"report_{batch_id}.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"  JSON saved: {json_path}")

    print("\n[STEP 4/4] Generating FDA HTML deviation report...")
    html_path = save_html_report(report, open_browser=open_report)
    print(f"  HTML saved: {html_path}")

    print(f"\n[COMPLETE] Report ID: {report['report_id']}")
    print("=" * 60)
    print(analysis[:2000])
    if len(analysis) > 2000:
        print("... [truncated — see HTML report for full analysis]")
    print("=" * 60)

    return report


def run_autonomous(open_report: bool = False) -> dict | None:
    print("=" * 60)
    print("  PharmaOps Agent — AUTONOMOUS MODE")
    print("  Splunk MCP detection → Gemini investigation → FDA report")
    print("=" * 60)

    print("\n[DETECT] Scanning Splunk for temperature anomalies...")
    anomaly = detect_top_anomaly()
    if not anomaly:
        print("[ERROR] No anomalies detected. Check Splunk index pharma_manufacturing.")
        return None

    print(f"\n[DETECT] Anomaly found!")
    print(f"  Batch:     {anomaly['batch_id']}")
    print(f"  Equipment: {anomaly['equipment_id']}")
    print(f"  Product:   {anomaly['product']}")
    print(f"  Deviations:{anomaly['deviation_count']} events")
    print(f"  Source:    {anomaly['detection_source']}")

    return investigate_batch(
        batch_id=anomaly["batch_id"],
        anomaly_type=anomaly["anomaly_type"],
        deviation_sigma=anomaly["deviation_sigma"],
        deviation_count=anomaly["deviation_count"],
        open_report=open_report,
    )


def run_demo(open_report: bool = False):
    print("=" * 60)
    print("  PharmaOps Agent — DEMO MODE (top 2 anomalies)")
    print("=" * 60)

    spl = (
        f"search index={SPLUNK_INDEX} source=temperature_logs.csv status=DEVIATION "
        "| stats count as deviation_count avg(temperature_C) as avg_temp "
        "by batch_id equipment_id product | sort -deviation_count | head 2"
    )
    result = search(spl)
    rows = result.get("rows", [])
    if not rows:
        from splunk_mcp import _local_detect_anomalies
        rows = _local_detect_anomalies()[:2]

    for row in rows:
        count = int(row.get("deviation_count", row.get("count", 3)))
        avg = float(row.get("avg_temp", 42))
        sigma = round(abs(avg - 42.5) / 2.5, 1)
        investigate_batch(
            batch_id=row["batch_id"],
            deviation_sigma=max(sigma, 2.0),
            deviation_count=count,
            open_report=open_report,
        )


def main():
    parser = argparse.ArgumentParser(description="PharmaOps Autonomous GMP Investigator")
    parser.add_argument("--autonomous", action="store_true", help="Detect and investigate top anomaly")
    parser.add_argument("--demo", action="store_true", help="Investigate top 2 anomalies")
    parser.add_argument("--batch", type=str, help="Investigate a specific batch ID")
    parser.add_argument("--open-report", action="store_true", help="Open HTML report in browser")
    args = parser.parse_args()

    if not os.getenv("GEMINI_API_KEY"):
        print("[ERROR] Set GEMINI_API_KEY environment variable.")
        sys.exit(1)

    if args.autonomous:
        run_autonomous(open_report=args.open_report)
    elif args.batch:
        investigate_batch(args.batch, open_report=args.open_report)
    elif args.demo:
        run_demo(open_report=args.open_report)
    else:
        run_autonomous(open_report=args.open_report)


if __name__ == "__main__":
    main()
