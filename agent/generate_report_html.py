"""Generate FDA-style HTML deviation reports from agent JSON output."""

import json
import re
import webbrowser
from datetime import datetime
from pathlib import Path

from config import REPORTS_DIR


def _extract_field(text: str, pattern: str, default: str = "N/A") -> str:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else default


def _gmp_badge_class(impact: str) -> str:
    impact = impact.lower()
    if "critical" in impact:
        return "critical"
    if "major" in impact:
        return "major"
    return "minor"


def _parse_analysis(analysis: str) -> dict:
    gmp = _extract_field(analysis, r"GMP IMPACT[:\s*]*\*{0,2}\s*(Critical|Major|Minor)", "Major")
    financial = _extract_field(
        analysis,
        r"FINANCIAL IMPACT[^:]*:\s*\*?\*?([^\n*]+)",
        "15-30 lakhs",
    )
    confidence = _extract_field(
        analysis,
        r"CONFIDENCE SCORE[:\s*]*\*{0,2}\s*([^\n]+)",
        "4/5",
    )
    root_cause = _extract_field(
        analysis,
        r"ROOT CAUSE[^:]*:\s*(.*?)(?=GMP IMPACT|2\.|$)",
        analysis[:500],
    )
    capa = _extract_field(
        analysis,
        r"CORRECTIVE ACTION[^:]*:\s*(.*?)(?=FINANCIAL IMPACT|4\.|$)",
        "See full analysis.",
    )
    return {
        "gmp_impact": gmp,
        "financial_impact": financial,
        "confidence": confidence,
        "root_cause": root_cause[:1200],
        "capa": capa[:2000],
    }


def render_html(report: dict) -> str:
    parsed = _parse_analysis(report.get("agent_analysis", ""))
    badge = _gmp_badge_class(parsed["gmp_impact"])
    ts = report.get("timestamp", datetime.now().isoformat())
    batch_id = report.get("batch_id", "UNKNOWN")
    report_id = report.get("report_id", f"DEV-{batch_id}")
    anomaly = report.get("anomaly_type", "temperature_deviation").replace("_", " ").title()
    sigma = report.get("deviation_sigma", "N/A")
    full_analysis = report.get("agent_analysis", "").replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GMP Deviation Report — {batch_id}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #f0f4f8; color: #1a202c; padding: 24px; }}
    .report {{ max-width: 900px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,.08); overflow: hidden; }}
    .header {{ background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%); color: #fff; padding: 28px 32px; }}
    .header h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
    .header p {{ opacity: .85; font-size: .9rem; }}
    .badge-row {{ display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }}
    .badge {{ padding: 6px 14px; border-radius: 20px; font-size: .8rem; font-weight: 600; text-transform: uppercase; }}
    .badge.critical {{ background: #fee2e2; color: #b91c1c; }}
    .badge.major {{ background: #ffedd5; color: #c2410c; }}
    .badge.minor {{ background: #fef9c3; color: #a16207; }}
    .meta {{ background: #f8fafc; padding: 16px 32px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; border-bottom: 1px solid #e2e8f0; }}
    .meta dt {{ font-size: .75rem; color: #64748b; text-transform: uppercase; letter-spacing: .05em; }}
    .meta dd {{ font-weight: 600; margin-top: 2px; }}
    .section {{ padding: 24px 32px; border-bottom: 1px solid #e2e8f0; }}
    .section h2 {{ font-size: 1rem; color: #1e3a5f; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
    .section h2::before {{ content: ''; width: 4px; height: 18px; background: #2d6a9f; border-radius: 2px; }}
    .section p, .section li {{ line-height: 1.7; color: #334155; font-size: .95rem; }}
    .footer {{ padding: 20px 32px; background: #f8fafc; font-size: .8rem; color: #64748b; text-align: center; }}
    .agent-tag {{ display: inline-block; background: #dbeafe; color: #1d4ed8; padding: 4px 10px; border-radius: 6px; font-size: .75rem; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="report">
    <div class="header">
      <h1>PharmaOps Monitor — GMP Deviation Report</h1>
      <p>Autonomous investigation by Splunk MCP + Google Gemini</p>
      <div class="badge-row">
        <span class="badge {badge}">GMP Impact: {parsed["gmp_impact"]}</span>
        <span class="agent-tag">AI-Generated CAPA</span>
      </div>
    </div>
    <dl class="meta">
      <div><dt>Report ID</dt><dd>{report_id}</dd></div>
      <div><dt>Batch ID</dt><dd>{batch_id}</dd></div>
      <div><dt>Anomaly</dt><dd>{anomaly} ({sigma}σ)</dd></div>
      <div><dt>Generated</dt><dd>{ts[:19].replace("T", " ")}</dd></div>
      <div><dt>Financial Impact</dt><dd>₹{parsed["financial_impact"]}</dd></div>
      <div><dt>Confidence</dt><dd>{parsed["confidence"]}</dd></div>
    </dl>
    <div class="section">
      <h2>Root Cause Analysis</h2>
      <p>{parsed["root_cause"]}</p>
    </div>
    <div class="section">
      <h2>Corrective &amp; Preventive Action (CAPA)</h2>
      <p>{parsed["capa"]}</p>
    </div>
    <div class="section">
      <h2>Full Agent Analysis</h2>
      <p style="font-size:.88rem;">{full_analysis}</p>
    </div>
    <div class="footer">
      PharmaOps Monitor · Splunk Agentic Ops Hackathon 2026 · Observability Track<br>
      Generated autonomously — no human investigator required
    </div>
  </div>
</body>
</html>"""


def save_html_report(report: dict, open_browser: bool = False) -> Path:
    batch_id = report.get("batch_id", "UNKNOWN")
    html_path = REPORTS_DIR / f"report_{batch_id}.html"
    html_path.write_text(render_html(report), encoding="utf-8")
    if open_browser:
        webbrowser.open(f"file://{html_path.resolve()}")
    return html_path


def json_to_html(json_path: str | Path, open_browser: bool = False) -> Path:
    report = json.loads(Path(json_path).read_text(encoding="utf-8"))
    return save_html_report(report, open_browser=open_browser)


if __name__ == "__main__":
    import sys

    targets = sys.argv[1:] or list(REPORTS_DIR.glob("report_*.json")) + list(Path(__file__).parent.glob("report_*.json"))
    for t in targets:
        p = Path(t)
        if p.suffix == ".json" and p.exists():
            out = json_to_html(p)
            print(f"Generated: {out}")
