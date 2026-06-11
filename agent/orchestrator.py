"""
PharmaOps End-to-End AI Agent Orchestrator

Full pipeline:
  1. Health check (MCP / REST / CSV)
  2. Autonomous anomaly detection
  3. Multi-source evidence collection
  4. Gemini reasoning + CAPA
  5. FDA HTML report generation
  6. Optional alert notification
"""

import json
import os
from datetime import datetime
from pathlib import Path

from google import genai

from config import GEMINI_MODEL, REPORTS_DIR, SPLUNK_INDEX
from generate_report_html import save_html_report
from splunk_mcp import clean_evidence, detect_top_anomaly, health_check, search

_client = None


def _gemini():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def check_system() -> dict:
    """Step 0: Verify all components."""
    h = health_check()
    h["gemini"] = bool(os.getenv("GEMINI_API_KEY"))
    h["ready"] = h["gemini"] and (h["mcp"] or h["splunk_rest"] or h["csv"])
    return h


def collect_evidence(batch_id: str) -> dict:
    """Step 2: Multi-source Splunk evidence gathering."""
    queries = {
        "temperature_stats": (
            f"search index={SPLUNK_INDEX} source=temperature_logs.csv batch_id=\"{batch_id}\" "
            "| stats avg(temperature_C) as avg_temp max(temperature_C) as max_temp "
            "min(temperature_C) as min_temp count as readings by equipment_id product"
        ),
        "temperature_deviations": (
            f"search index={SPLUNK_INDEX} source=temperature_logs.csv batch_id=\"{batch_id}\" status=DEVIATION "
            "| table timestamp temperature_C equipment_id status | head 10"
        ),
        "batch_qc": (
            f"search index={SPLUNK_INDEX} source=batch_summary.csv batch_id=\"{batch_id}\" "
            "| table batch_id product yield_pct deviation_count batch_status oee_score failure_mode"
        ),
        "moisture": (
            f"search index={SPLUNK_INDEX} source=moisture_logs.csv batch_id=\"{batch_id}\" "
            "| stats avg(moisture_pct) as avg_moisture max(moisture_pct) as max_moisture "
            "count as readings by equipment_id"
        ),
        "equipment_downtime": (
            f"search index={SPLUNK_INDEX} source=equipment_downtime.csv "
            "| stats sum(downtime_minutes) as total_downtime count as events by equipment_id "
            "| sort -total_downtime | head 5"
        ),
    }

    evidence = {}
    for name, spl in queries.items():
        result = search(spl)
        evidence[name] = {
            "source": result.get("source", "unknown"),
            "rows": result.get("rows", [])[:10],
        }
    return evidence


def reason_and_report(
    batch_id: str,
    anomaly_type: str,
    deviation_sigma: float,
    deviation_count: int,
    evidence: dict,
    detection_source: str = "unknown",
) -> dict:
    """Step 3-4: Gemini analysis + structured report."""
    clean = clean_evidence(evidence)

    prompt = f"""You are PharmaOps Agent, an autonomous FDA GMP compliance investigator.

BATCH UNDER INVESTIGATION: {batch_id}
Anomaly: {anomaly_type} | Severity: {deviation_sigma} sigma | Events: {deviation_count}
Detection source: {detection_source}
Time: {datetime.now().isoformat()}

SPLUNK MANUFACTURING EVIDENCE (all sources consistent for this batch):
{json.dumps(clean, indent=2)}

Write a professional GMP deviation report. All data sources share the same batch_id and product — treat as one manufacturing run.

Structure your response EXACTLY as:

**1. ROOT CAUSE**
Evidence-based analysis citing specific temperature values, timestamps, equipment IDs.

**2. GMP IMPACT: Critical / Major / Minor**
Justification based on patient safety and batch release risk.

**3. CORRECTIVE ACTION (CAPA)**
Immediate containment actions (numbered list).
Preventive actions (numbered list).

**4. FINANCIAL IMPACT:** X-Y lakhs (INR)
Brief cost breakdown.

**5. CONFIDENCE SCORE: X/5**
Reasoning for confidence level.

Be specific. Use numbers from the evidence. Do not mention HTTP errors or data inconsistencies unless truly present in evidence."""

    response = _gemini().models.generate_content(model=GEMINI_MODEL, contents=prompt)

    report = {
        "report_id": f"DEV-{batch_id}-{datetime.now().strftime('%Y%m%d%H%M')}",
        "batch_id": batch_id,
        "anomaly_type": anomaly_type,
        "deviation_sigma": deviation_sigma,
        "deviation_count": deviation_count,
        "detection_source": detection_source,
        "timestamp": datetime.now().isoformat(),
        "evidence": clean,
        "agent_analysis": response.text,
    }
    return report


def save_report(report: dict, open_browser: bool = False) -> tuple[Path, Path]:
    """Step 5: Persist JSON + HTML report."""
    batch_id = report["batch_id"]
    json_path = REPORTS_DIR / f"report_{batch_id}.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    html_path = save_html_report(report, open_browser=open_browser)
    return json_path, html_path


def run_full_pipeline(open_browser: bool = False, log=print) -> dict | None:
    """End-to-end autonomous agent: detect → investigate → report."""

    log("=" * 60)
    log("  PharmaOps AI Agent — END-TO-END PIPELINE")
    log("=" * 60)

    # Step 0: Health
    log("\n[STEP 0] System health check...")
    health = check_system()
    log(f"  MCP:         {'OK' if health['mcp'] else 'unavailable'}")
    log(f"  Splunk REST: {'OK' if health['splunk_rest'] else 'unavailable'}")
    log(f"  Local CSV:   {'OK' if health['csv'] else 'unavailable'}")
    log(f"  Gemini:      {'OK' if health['gemini'] else 'MISSING API KEY'}")
    log(f"  Using:       {health['recommended']}")

    if not health["ready"]:
        log("[ERROR] System not ready. Set GEMINI_API_KEY and ensure Splunk or CSV data exists.")
        return None

    # Step 1: Detect
    log("\n[STEP 1] Autonomous anomaly detection...")
    anomaly = detect_top_anomaly()
    if not anomaly:
        log("[ERROR] No anomalies found.")
        return None

    log(f"  Batch:      {anomaly['batch_id']}")
    log(f"  Product:    {anomaly['product']}")
    log(f"  Equipment:  {anomaly['equipment_id']}")
    log(f"  Deviations: {anomaly['deviation_count']}")
    log(f"  Source:     {anomaly['detection_source']}")

    # Step 2: Evidence
    log("\n[STEP 2] Collecting multi-source evidence...")
    evidence = collect_evidence(anomaly["batch_id"])
    for k, v in evidence.items():
        log(f"  {k}: {len(v.get('rows', []))} rows via {v.get('source')}")

    # Step 3-4: Reason
    log("\n[STEP 3] Gemini reasoning + CAPA generation...")
    report = reason_and_report(
        batch_id=anomaly["batch_id"],
        anomaly_type=anomaly["anomaly_type"],
        deviation_sigma=anomaly["deviation_sigma"],
        deviation_count=anomaly["deviation_count"],
        evidence=evidence,
        detection_source=anomaly["detection_source"],
    )

    # Step 5: Save
    log("\n[STEP 4] Generating FDA HTML report...")
    json_path, html_path = save_report(report, open_browser=open_browser)
    log(f"  JSON: {json_path}")
    log(f"  HTML: {html_path}")

    # Step 6: Alert log
    alert = {
        "alert_id": f"ALERT-{anomaly['batch_id']}-{datetime.now().strftime('%Y%m%d%H%M')}",
        "batch_id": anomaly["batch_id"],
        "severity": "HIGH",
        "report_id": report["report_id"],
        "timestamp": datetime.now().isoformat(),
        "message": f"GMP deviation detected on {anomaly['batch_id']} — autonomous investigation complete.",
    }
    alert_path = REPORTS_DIR / "alerts.jsonl"
    with open(alert_path, "a") as f:
        f.write(json.dumps(alert) + "\n")
    log(f"\n[STEP 5] Alert logged → {alert_path}")
    log(f"\n[COMPLETE] Report {report['report_id']}")

    return report


def investigate_batch(
    batch_id: str,
    deviation_count: int = 0,
    deviation_sigma: float = 2.5,
    open_browser: bool = False,
    log=print,
) -> dict:
    """Investigate a specific batch end-to-end."""
    log(f"\n[AGENT] Investigating {batch_id}...")
    evidence = collect_evidence(batch_id)
    report = reason_and_report(
        batch_id=batch_id,
        anomaly_type="temperature_deviation",
        deviation_sigma=deviation_sigma,
        deviation_count=deviation_count,
        evidence=evidence,
    )
    save_report(report, open_browser=open_browser)
    return report
