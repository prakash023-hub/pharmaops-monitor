"""Generate FDA-style HTML deviation reports from agent JSON output."""

import html as html_lib
import json
import re
import webbrowser
from datetime import datetime
from pathlib import Path

from config import REPORTS_DIR


def _inline_markdown(text: str) -> str:
    text = html_lib.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def markdown_to_html(text: str) -> str:
    """Convert Gemini markdown analysis to clean HTML."""
    if not text:
        return "<p>No analysis available.</p>"

    lines = text.split("\n")
    parts: list[str] = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            parts.append("</ul>")
            in_list = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            close_list()
            continue

        if re.match(r"^\*\*\d+\.", stripped) or re.match(r"^#{1,3}\s", stripped):
            close_list()
            title = re.sub(r"^\*\*|\*\*$|^#+\s*", "", stripped).strip("* ")
            parts.append(f'<h3 class="section-title">{_inline_markdown(title)}</h3>')
            continue

        if re.match(r"^\*\s+", stripped):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            item = re.sub(r"^\*\s+", "", stripped)
            parts.append(f"<li>{_inline_markdown(item)}</li>")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            close_list()
            parts.append(f'<p class="numbered">{_inline_markdown(stripped)}</p>')
            continue

        close_list()
        parts.append(f"<p>{_inline_markdown(stripped)}</p>")

    close_list()
    return "\n".join(parts)


def _extract_section(analysis: str, number: int, name: str) -> str:
    patterns = [
        rf"\*\*{number}\.\s*{name}[^*]*\*\*(.*?)(?=\*\*{number + 1}\.|\Z)",
        rf"{number}\.\s*{name}[:\s]*(.*?)(?={number + 1}\.|CONFIDENCE|FINANCIAL|\Z)",
    ]
    for pattern in patterns:
        match = re.search(pattern, analysis, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""


def _parse_analysis(analysis: str) -> dict:
    gmp_match = re.search(r"GMP IMPACT[:\s*]*\*{0,2}\s*(Critical|Major|Minor)", analysis, re.I)
    gmp = gmp_match.group(1) if gmp_match else "Major"

    fin_match = re.search(
        r"(?:\*\*)?4\.\s*FINANCIAL IMPACT[:\s*]*\*{0,2}\s*([^\n]+)",
        analysis,
        re.I,
    )
    financial = fin_match.group(1).strip("* ") if fin_match else "15-30 lakhs"
    financial = re.sub(r"\(.*?\)$", "", financial).strip()

    conf_match = re.search(
        r"(?:\*\*)?5\.\s*CONFIDENCE SCORE[:\s*]*\*{0,2}\s*([\d.]+/\d+)",
        analysis,
        re.I,
    )
    confidence = conf_match.group(1) if conf_match else "4/5"

    root_cause = _extract_section(analysis, 1, "ROOT CAUSE")
    capa = _extract_section(analysis, 3, "CORRECTIVE ACTION")

    if not root_cause:
        root_cause = _extract_section(analysis, 1, "ROOT CAUSE \\(evidence-based\\)")
    if not capa:
        capa = _extract_section(analysis, 3, "CORRECTIVE ACTION \\(CAPA\\)")

    return {
        "gmp_impact": gmp,
        "financial_impact": financial,
        "confidence": confidence,
        "root_cause_html": markdown_to_html(root_cause) if root_cause else "",
        "capa_html": markdown_to_html(capa) if capa else "",
        "full_html": markdown_to_html(analysis),
    }


def _gmp_badge_class(impact: str) -> str:
    impact = impact.lower()
    if "critical" in impact:
        return "critical"
    if "major" in impact:
        return "major"
    return "minor"


def render_html(report: dict) -> str:
    analysis = report.get("agent_analysis", "")
    parsed = _parse_analysis(analysis)
    badge = _gmp_badge_class(parsed["gmp_impact"])
    ts = report.get("timestamp", datetime.now().isoformat())
    batch_id = report.get("batch_id", "UNKNOWN")
    report_id = report.get("report_id", f"DEV-{batch_id}")
    anomaly = report.get("anomaly_type", "temperature_deviation").replace("_", " ").title()
    sigma = report.get("deviation_sigma", "N/A")
    dev_count = report.get("deviation_count", "N/A")
    impact = report.get("impact", {})
    qa = report.get("agents", {}).get("qa_review", {})
    if impact.get("display"):
        parsed["financial_impact"] = impact["display"]
    if qa.get("confidence_adjusted"):
        parsed["confidence"] = str(qa["confidence_adjusted"])

    agents_badge = ""
    if report.get("agents"):
        qa_dec = qa.get("qa_decision", "PENDING")
        agents_badge = f'<span class="agent-tag">QA: {qa_dec}</span>'

    ich_reg = report.get("ich_regulatory", {})
    ich_risk = report.get("ich_risk", {})
    ich_qa = qa.get("ich_compliance", {})

    ich_html = ""
    if ich_reg or ich_risk:
        ich_items = "".join(
            f"<li><strong>ICH {code}</strong>: {status}</li>"
            for code, status in ich_qa.items()
        ) if ich_qa else ""
        ich_guidelines = "".join(
            f'<li><strong>{g.get("guideline", "")}</strong> — {g.get("title", "")}<br>'
            f'<span style="color:#64748b;font-size:0.85rem">{g.get("relevance", "")}</span></li>'
            for g in ich_reg.get("ich_guidelines", [])
        )
        ich_html = f"""
    <div class="section">
      <h2>ICH Regulatory Compliance (Q7 / Q8 / Q9 / Q10)</h2>
      <div class="content">
        <p><strong>CQA Affected (ICH Q8):</strong> {ich_reg.get("cqa", "N/A")}</p>
        <p><strong>ICH Q9 Risk Level:</strong> {ich_risk.get("risk_level", "N/A")}
           (RPN={ich_risk.get("rpn", "N/A")} — {ich_risk.get("method", "")})</p>
        <p>{ich_reg.get("risk_statement", "")}</p>
        <h3 class="section-title">ICH QA Compliance Assessment</h3>
        <ul>{ich_items}</ul>
        <h3 class="section-title">Applicable ICH Guidelines</h3>
        <ul>{ich_guidelines}</ul>
        <p style="font-size:0.85rem;color:#64748b">Also: FDA 21 CFR Part 211 — {", ".join(qa.get("fda_citations", []))}</p>
      </div>
    </div>"""

    root_html = parsed["root_cause_html"] or parsed["full_html"]
    capa_html = parsed["capa_html"] or "<p>See full analysis below.</p>"

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
    .meta {{ background: #f8fafc; padding: 16px 32px; display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; border-bottom: 1px solid #e2e8f0; }}
    .meta dt {{ font-size: .75rem; color: #64748b; text-transform: uppercase; letter-spacing: .05em; }}
    .meta dd {{ font-weight: 600; margin-top: 2px; font-size: .9rem; }}
    .section {{ padding: 24px 32px; border-bottom: 1px solid #e2e8f0; }}
    .section h2 {{ font-size: 1rem; color: #1e3a5f; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
    .section h2::before {{ content: ''; width: 4px; height: 18px; background: #2d6a9f; border-radius: 2px; }}
    .content h3.section-title {{ font-size: .9rem; color: #475569; margin: 16px 0 8px; font-weight: 600; }}
    .content p {{ line-height: 1.75; color: #334155; font-size: .93rem; margin-bottom: 10px; }}
    .content ul {{ margin: 8px 0 12px 20px; }}
    .content li {{ line-height: 1.75; color: #334155; font-size: .93rem; margin-bottom: 6px; }}
    .content strong {{ color: #1e293b; }}
    .content code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: .85rem; }}
    .footer {{ padding: 20px 32px; background: #f8fafc; font-size: .8rem; color: #64748b; text-align: center; }}
    .agent-tag {{ display: inline-block; background: #dbeafe; color: #1d4ed8; padding: 4px 10px; border-radius: 6px; font-size: .75rem; font-weight: 600; }}
  </style>
</head>
<body>
  <div class="report">
    <div class="header">
      <h1>PharmaOps Monitor — GMP Deviation Report</h1>
      <p>Autonomous investigation — Splunk MCP + Gemini | FDA 21 CFR + ICH Q7/Q8/Q9/Q10</p>
      <div class="badge-row">
        <span class="badge {badge}">GMP Impact: {parsed["gmp_impact"]}</span>
        <span class="agent-tag">AI-Generated CAPA</span>
        {agents_badge}
      </div>
    </div>
    <dl class="meta">
      <div><dt>Report ID</dt><dd>{report_id}</dd></div>
      <div><dt>Batch ID</dt><dd>{batch_id}</dd></div>
      <div><dt>Anomaly</dt><dd>{anomaly} ({sigma}σ)</dd></div>
      <div><dt>Deviation Events</dt><dd>{dev_count}</dd></div>
      <div><dt>Generated</dt><dd>{ts[:19].replace("T", " ")}</dd></div>
      <div><dt>Financial Impact</dt><dd>₹{parsed["financial_impact"]}</dd></div>
      <div><dt>Confidence</dt><dd>{parsed["confidence"]}</dd></div>
    </dl>
    <div class="section">
      <h2>Root Cause Analysis</h2>
      <div class="content">{root_html}</div>
    </div>
    {ich_html}
    <div class="section">
      <h2>Corrective &amp; Preventive Action (CAPA per ICH Q10)</h2>
      <div class="content">{capa_html}</div>
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

    targets = sys.argv[1:] or list(REPORTS_DIR.glob("report_*.json"))
    for t in targets:
        p = Path(t)
        if p.suffix == ".json" and p.exists():
            out = json_to_html(p)
            print(f"Generated: {out}")
