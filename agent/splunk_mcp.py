"""Splunk MCP client with CSV fallback for offline demos."""

import json
import re
import ssl
import urllib.request
from typing import Any

import pandas as pd

from config import CSV_SOURCES, SPLUNK_INDEX, SPLUNK_MCP_URL, load_mcp_token


def _mcp_request(spl: str, earliest: str = "-30d", latest: str = "now") -> dict:
    token = load_mcp_token()
    if not token:
        return {"error": "MCP token not found. Set SPLUNK_MCP_TOKEN or ~/mcp_token.txt"}

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

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
        resp = urllib.request.urlopen(req, context=ctx, timeout=60)
        return json.loads(resp.read())
    except Exception as exc:
        return {"error": str(exc)}


def _extract_rows(response: dict) -> list[dict]:
    if "error" in response:
        return []

    result = response.get("result", response)
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
    for source in CSV_SOURCES:
        if source in spl:
            return source
    return None


def _csv_fallback(spl: str) -> list[dict]:
    source = _infer_source(spl)
    if not source or not CSV_SOURCES[source].exists():
        return _local_detect_anomalies() if "DEVIATION" in spl.upper() else []

    df = pd.read_csv(CSV_SOURCES[source])
    spl_lower = spl.lower()

    if "batch_status=fail" in spl_lower or "batch_status=\"fail\"" in spl_lower:
        out = df[df["batch_status"] == "FAIL"].head(10)
        return out.to_dict(orient="records")

    if "status=deviation" in spl_lower or 'status="deviation"' in spl_lower:
        if "stats count" in spl_lower or "deviation_count" in spl_lower:
            group_cols = ["batch_id", "equipment_id"]
            if "product" in df.columns:
                group_cols.append("product")
            agg = (
                df[df["status"] == "DEVIATION"]
                .groupby(group_cols, as_index=False)
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
                if col in agg.columns:
                    agg[col] = agg[col].round(2)
            return agg.to_dict(orient="records")
        out = df[df["status"] == "DEVIATION"].head(20)
        return out.to_dict(orient="records")

    if "downtime_minutes" in spl_lower and "stats" in spl_lower:
        out = (
            df.groupby("equipment_id", as_index=False)["downtime_minutes"]
            .sum()
            .rename(columns={"downtime_minutes": "total"})
            .sort_values("total", ascending=False)
        )
        return out.to_dict(orient="records")

    if "batch_id=" in spl_lower:
        match = re.search(r'batch_id[=\\"]+([A-Z0-9-]+)', spl, re.I)
        if match:
            out = df[df["batch_id"] == match.group(1)]
            return out.to_dict(orient="records")

    if "stats count by source" in spl_lower:
        return [{"source": name, "count": len(CSV_SOURCES)} for name in CSV_SOURCES]

    return df.head(10).to_dict(orient="records")


def _local_detect_anomalies() -> list[dict]:
    path = CSV_SOURCES["temperature_logs.csv"]
    if not path.exists():
        return []
    df = pd.read_csv(path)
    dev = df[df["status"] == "DEVIATION"]
    out = (
        dev.groupby(["batch_id", "equipment_id", "product"], as_index=False)
        .agg(
            deviation_count=("status", "count"),
            avg_temp=("temperature_C", "mean"),
            max_temp=("temperature_C", "max"),
            min_temp=("temperature_C", "min"),
        )
        .sort_values("deviation_count", ascending=False)
        .head(5)
    )
    for _, row in out.iterrows():
        row["avg_temp"] = round(row["avg_temp"], 2)
        row["max_temp"] = round(row["max_temp"], 2)
        row["min_temp"] = round(row["min_temp"], 2)
    return out.to_dict(orient="records")


def search(spl: str, earliest: str = "-30d", latest: str = "now") -> dict:
    """Run SPL via Splunk MCP; fall back to local CSV if MCP unavailable."""
    if not spl.strip().lower().startswith("search"):
        spl = f"search {spl}"

    response = _mcp_request(spl, earliest, latest)
    rows = _extract_rows(response)

    if rows:
        return {"source": "mcp", "rows": rows, "raw": response}

    if "error" in response:
        fallback_rows = _csv_fallback(spl)
        if fallback_rows:
            return {
                "source": "csv_fallback",
                "rows": fallback_rows,
                "warning": response["error"],
            }
        return {"source": "error", "rows": [], "error": response["error"]}

    fallback_rows = _csv_fallback(spl)
    return {"source": "csv_fallback" if fallback_rows else "mcp", "rows": fallback_rows, "raw": response}


def detect_top_anomaly() -> dict | None:
    """Autonomously detect the batch with the most temperature deviations."""
    spl = (
        f"search index={SPLUNK_INDEX} source=temperature_logs.csv status=DEVIATION "
        "| stats count as deviation_count avg(temperature_C) as avg_temp "
        "max(temperature_C) as max_temp min(temperature_C) as min_temp "
        "by batch_id equipment_id product "
        "| sort -deviation_count | head 1"
    )
    result = search(spl)
    rows = result.get("rows", [])
    if not rows:
        rows = _local_detect_anomalies()
    if not rows:
        return None

    top = rows[0]
    count = int(top.get("deviation_count", top.get("count", 0)))
    avg = float(top.get("avg_temp", 42))
    spec_mid = 42.5
    sigma = round(abs(avg - spec_mid) / 2.5, 1) if avg else 2.5

    return {
        "batch_id": top["batch_id"],
        "equipment_id": top.get("equipment_id", "COAT-01"),
        "product": top.get("product", "Unknown"),
        "anomaly_type": "temperature_deviation",
        "deviation_count": count,
        "deviation_sigma": max(sigma, 2.0),
        "detection_source": result.get("source", "unknown"),
    }
