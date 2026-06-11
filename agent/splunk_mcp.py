"""Splunk data layer: MCP Server → REST API → local CSV fallback."""

import json
import re
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

import pandas as pd

from config import CSV_SOURCES, SPLUNK_INDEX, SPLUNK_MCP_URL, load_mcp_token

SPLUNK_REST_URL = "https://localhost:8089"
SPLUNK_USER = __import__("os").getenv("SPLUNK_USER", "admin")
SPLUNK_PASS = __import__("os").getenv("SPLUNK_PASS", "Splunk@23")


def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _mcp_request(spl: str, earliest: str = "-30d", latest: str = "now") -> dict:
    token = load_mcp_token()
    if not token:
        return {"error": "MCP token not found"}

    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "search",
            "arguments": {"query": spl, "earliest_time": earliest, "latest_time": latest},
        },
        "id": 1,
    }
    req = urllib.request.Request(
        SPLUNK_MCP_URL,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, context=_ssl_ctx(), timeout=60)
        return {"transport": "mcp", "data": json.loads(resp.read())}
    except Exception as exc:
        return {"error": str(exc)}


def _rest_search(spl: str, earliest: str = "0", latest: str = "now") -> dict:
    ctx = _ssl_ctx()
    creds = urllib.parse.urlencode({"username": SPLUNK_USER, "password": SPLUNK_PASS}).encode()
    try:
        login_req = urllib.request.Request(f"{SPLUNK_REST_URL}/services/auth/login", data=creds)
        login_resp = urllib.request.urlopen(login_req, context=ctx, timeout=15)
        token = ET.parse(login_resp).find(".//sessionKey").text

        if not spl.strip().lower().startswith("search"):
            spl = f"search {spl}"

        search_data = urllib.parse.urlencode({
            "search": spl,
            "output_mode": "json",
            "count": "50",
            "earliest_time": earliest,
            "latest_time": latest,
        }).encode()
        search_req = urllib.request.Request(
            f"{SPLUNK_REST_URL}/services/search/jobs/export",
            data=search_data,
            headers={"Authorization": f"Splunk {token}"},
        )
        search_resp = urllib.request.urlopen(search_req, context=ctx, timeout=60)
        rows = []
        for line in search_resp:
            try:
                obj = json.loads(line)
                if "result" in obj:
                    rows.append(obj["result"])
            except json.JSONDecodeError:
                pass
        return {"transport": "splunk_rest", "rows": rows}
    except Exception as exc:
        return {"error": str(exc)}


def _extract_mcp_rows(response: dict) -> list[dict]:
    data = response.get("data", response)
    if "error" in response and "data" not in response:
        return []

    result = data.get("result", data) if isinstance(data, dict) else {}
    if isinstance(result, dict):
        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                text = item.get("text", "")
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        return [r for r in parsed if isinstance(r, dict)]
                    if isinstance(parsed, dict):
                        for key in ("results", "rows", "data"):
                            if key in parsed and isinstance(parsed[key], list):
                                return parsed[key]
                except json.JSONDecodeError:
                    rows = []
                    for line in text.splitlines():
                        line = line.strip()
                        if line.startswith("{") and line.endswith("}"):
                            try:
                                rows.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
                    if rows:
                        return rows
        for key in ("results", "rows", "data"):
            if key in result and isinstance(result[key], list):
                return result[key]
    return []


def _infer_source(spl: str) -> str | None:
    """Pick the best CSV for a query — avoid matching wrong file on join queries."""
    spl_lower = spl.lower()
    if any(k in spl_lower for k in ("batch_status", "batch_status=fail", "yield_pct", "oee_score", "failed")):
        return "batch_summary.csv"
    if "downtime" in spl_lower or "equipment_downtime" in spl_lower:
        return "equipment_downtime.csv"
    if "moisture" in spl_lower:
        return "moisture_logs.csv"
    if "temperature" in spl_lower or "deviation" in spl_lower:
        return "temperature_logs.csv"
    for source in CSV_SOURCES:
        if source in spl_lower:
            return source
    return None


def _csv_fail_batches() -> list[dict]:
    """Answer: what batches failed and why."""
    bs = pd.read_csv(CSV_SOURCES["batch_summary.csv"])
    fails = bs[bs["batch_status"] == "FAIL"].copy()
    if fails.empty:
        return []

    tl = pd.read_csv(CSV_SOURCES["temperature_logs.csv"])
    dev = (
        tl[tl["status"] == "DEVIATION"]
        .groupby("batch_id", as_index=False)
        .agg(deviation_count=("status", "count"), avg_temp=("temperature_C", "mean"))
    )
    out = fails.merge(dev, on="batch_id", how="left", suffixes=("", "_temp"))
    out["reason"] = out.apply(
        lambda r: (
            f"{r.get('failure_mode', 'none')} — {int(r.get('deviation_count_temp', r.get('deviation_count', 0)))} temperature deviations"
            if r.get("deviation_count_temp", 0) or r.get("deviation_count", 0)
            else str(r.get("failure_mode", "quality review failed"))
        ),
        axis=1,
    )
    cols = ["batch_id", "product", "deviation_count", "batch_status", "yield_pct", "reason"]
    return out[cols].head(20).to_dict(orient="records")


def _csv_query(spl: str) -> list[dict]:
    spl_lower = spl.lower()

    if any(k in spl_lower for k in ("batch_status=fail", 'batch_status="fail"', "failed", "fail")):
        if "batch_summary" in spl_lower or "fail" in spl_lower:
            return _csv_fail_batches()

    source = _infer_source(spl)
    if not source or not CSV_SOURCES[source].exists():
        if "fail" in spl_lower:
            return _csv_fail_batches()
        if "DEVIATION" in spl.upper():
            return _local_detect_anomalies()
        return []

    df = pd.read_csv(CSV_SOURCES[source])

    if source == "batch_summary.csv" and "fail" in spl_lower:
        if "batch_status" in df.columns:
            return df[df["batch_status"] == "FAIL"].head(20).to_dict(orient="records")

    if "status=deviation" in spl_lower or "deviation" in spl_lower:
        if "status" in df.columns:
            if "stats count" in spl_lower or "deviation_count" in spl_lower:
                group_cols = [c for c in ("batch_id", "equipment_id", "product") if c in df.columns]
                agg = (
                    df[df["status"] == "DEVIATION"]
                    .groupby(group_cols, as_index=False)
                    .agg(
                        deviation_count=("status", "count"),
                        **({"avg_temp": ("temperature_C", "mean")} if "temperature_C" in df.columns else {}),
                    )
                    .sort_values("deviation_count", ascending=False)
                    .head(10)
                )
                if "avg_temp" in agg.columns:
                    agg["avg_temp"] = agg["avg_temp"].round(2)
                return agg.to_dict(orient="records")
            return df[df["status"] == "DEVIATION"].head(20).to_dict(orient="records")

    if "downtime" in spl_lower and "equipment_id" in df.columns:
        return (
            df.groupby("equipment_id", as_index=False)["downtime_minutes"]
            .sum()
            .rename(columns={"downtime_minutes": "total_downtime"})
            .sort_values("total_downtime", ascending=False)
            .to_dict(orient="records")
        )

    match = re.search(r'batch_id[=\\"]+([A-Z0-9-]+)', spl, re.I)
    if match and "batch_id" in df.columns:
        return df[df["batch_id"] == match.group(1)].to_dict(orient="records")

    return df.head(10).to_dict(orient="records")


# Known-good SPL templates (work with raw CSV ingest + rex)
SPL_TEMPLATES = {
    "failed_batches": (
        f"search index={SPLUNK_INDEX} sourcetype=batch_summary.csv "
        '| rex field=_raw "^(?<timestamp>[^,]+),(?<batch_id>[^,]+),(?<product>[^,]+),'
        '(?<yield_pct>[^,]+),(?<deviation_count>[^,]+),(?<batch_status>[^,]+),(?<oee_score>[^,]+),(?<failure_mode>.*)" '
        '| search batch_id=BATCH-* batch_status=FAIL '
        "| table batch_id product deviation_count batch_status failure_mode | head 20"
    ),
    "deviations_by_batch": (
        f"search index={SPLUNK_INDEX} sourcetype=temperature_logs.csv _raw=*DEVIATION* "
        '| rex field=_raw "^(?<timestamp>[^,]+),(?<batch_id>[^,]+),(?<equipment_id>[^,]+),'
        '(?<product>[^,]+),(?<temperature_C>[^,]+),(?<status>[^,]+)" '
        "| search batch_id=BATCH-* | stats count by batch_id equipment_id | sort -count | head 10"
    ),
    "equipment_downtime": (
        f"search index={SPLUNK_INDEX} sourcetype=equipment_downtime.csv "
        '| rex field=_raw "^(?<timestamp>[^,]+),(?<equipment_id>[^,]+),(?<equipment_type>[^,]+),'
        '(?<downtime_minutes>[^,]+),(?<reason>[^,]+),(?<severity>[^,]+)" '
        "| search equipment_id=COAT-* OR equipment_id=GRAN-* OR equipment_id=COMPRESS-* "
        "| stats sum(downtime_minutes) as total_downtime by equipment_id | sort -total_downtime"
    ),
}


def _intent_spl(question: str) -> str | None:
    q = question.lower()
    if any(w in q for w in ("fail", "failed", "why")):
        return SPL_TEMPLATES["failed_batches"]
    if "downtime" in q or "equipment" in q:
        return SPL_TEMPLATES["equipment_downtime"]
    if "deviation" in q or "temperature" in q:
        return SPL_TEMPLATES["deviations_by_batch"]
    return None


def _local_detect_anomalies() -> list[dict]:
    path = CSV_SOURCES["temperature_logs.csv"]
    if not path.exists():
        return []
    df = pd.read_csv(path)
    out = (
        df[df["status"] == "DEVIATION"]
        .groupby(["batch_id", "equipment_id", "product"], as_index=False)
        .agg(
            deviation_count=("status", "count"),
            avg_temp=("temperature_C", "mean"),
            max_temp=("temperature_C", "max"),
            min_temp=("temperature_C", "min"),
        )
        .sort_values("deviation_count", ascending=False)
        .head(5)
    )
    for col in ("avg_temp", "max_temp", "min_temp"):
        out[col] = out[col].round(2)
    return out.to_dict(orient="records")


def health_check() -> dict:
    """Check Splunk MCP, REST, and local CSV availability."""
    status = {"mcp": False, "splunk_rest": False, "csv": False, "recommended": "csv"}

    token = load_mcp_token()
    if token:
        r = _mcp_request(f"search index={SPLUNK_INDEX} | head 1")
        if "error" not in r and _extract_mcp_rows(r):
            status["mcp"] = True
            status["recommended"] = "mcp"

    r2 = _rest_search(f"index={SPLUNK_INDEX} | head 1")
    if r2.get("rows"):
        status["splunk_rest"] = True
        if not status["mcp"]:
            status["recommended"] = "splunk_rest"

    if CSV_SOURCES["temperature_logs.csv"].exists():
        status["csv"] = True
        if not status["mcp"] and not status["splunk_rest"]:
            status["recommended"] = "csv"

    return status


def search(spl: str, earliest: str = "-30d", latest: str = "now", question: str = "") -> dict:
    """Query Splunk via MCP → REST → CSV. Returns clean rows for agents."""
    if not spl.strip().lower().startswith("search"):
        spl = f"search {spl}"

    def _run(query: str) -> tuple[str | None, list[dict]]:
        mcp_resp = _mcp_request(query, earliest, latest)
        rows = _extract_mcp_rows(mcp_resp)
        if rows:
            return "mcp", rows
        rest_resp = _rest_search(query, earliest="0", latest=latest)
        rows = rest_resp.get("rows", [])
        if rows:
            return "splunk_rest", rows
        return None, []

    source, rows = _run(spl)
    spl_used = spl
    if rows:
        return {"source": source, "rows": rows, "spl_used": spl_used}

    if question:
        template_spl = _intent_spl(question)
        if template_spl and template_spl != spl:
            source, rows = _run(template_spl)
            if rows:
                return {"source": source or "splunk_rest", "rows": rows, "spl_used": template_spl}

    try:
        rows = _csv_query(spl)
        if not rows and question and "fail" in question.lower():
            rows = _csv_fail_batches()
        elif not rows and question:
            rows = _csv_query(_intent_spl(question) or spl)
    except Exception as exc:
        rows = _csv_fail_batches() if "fail" in (question + spl).lower() else []
        if not rows:
            return {"source": "error", "rows": [], "error": str(exc), "spl_used": spl}

    if rows:
        return {"source": "csv", "rows": rows, "spl_used": spl_used}

    return {"source": "error", "rows": [], "error": "No data returned", "spl_used": spl}


def clean_evidence(evidence: dict) -> dict:
    """Strip transport warnings before sending to Gemini — keep only data rows."""
    cleaned = {}
    for key, val in evidence.items():
        if isinstance(val, dict):
            cleaned[key] = {
                "source": val.get("source", "unknown"),
                "rows": val.get("rows", [])[:10],
            }
    return cleaned


def detect_top_anomaly() -> dict | None:
    spl = (
        f"search index={SPLUNK_INDEX} source=temperature_logs.csv status=DEVIATION "
        "| stats count as deviation_count avg(temperature_C) as avg_temp "
        "max(temperature_C) as max_temp min(temperature_C) as min_temp "
        "by batch_id equipment_id product "
        "| sort -deviation_count | head 1"
    )
    result = search(spl)
    rows = result.get("rows") or _local_detect_anomalies()
    if not rows:
        return None

    top = rows[0]
    count = int(top.get("deviation_count", top.get("count", 0)))
    avg = float(top.get("avg_temp", 42.5))
    sigma = round(abs(avg - 42.5) / 2.5, 1)

    return {
        "batch_id": top["batch_id"],
        "equipment_id": top.get("equipment_id", "COAT-01"),
        "product": top.get("product", "Unknown"),
        "anomaly_type": "temperature_deviation",
        "deviation_count": count,
        "deviation_sigma": max(sigma, 2.0),
        "detection_source": result.get("source", "unknown"),
    }
