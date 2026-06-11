# Judge Demo — 5 Minutes

## One-Command Setup

```bash
git clone https://github.com/prakash023-hub/pharmaops-monitor
cd pharmaops-monitor
export GEMINI_API_KEY=your_key
chmod +x setup.sh && ./setup.sh
```

## Run Multi-Agent Demo (recommended)

```bash
./run_demo.sh
```

Shows:
1. **Detection Agent** — finds worst batch from Splunk
2. **Investigation Agent** — evidence + Gemini CAPA
3. **QA Review Agent** — FDA 21 CFR Part 211 validation
4. **FDA HTML report** — opens in browser
5. **Regulatory Intelligence** — GMP + QMS + PV scores + industry comparison
6. **Natural language chat** — 4 plant manager questions

## Regulatory Demo (GMP + QMS + PV) — 60 seconds

```bash
python3 scripts/run_regulatory_demo.py --open
```

Opens `agent/reports/regulatory_BATCH-1027.html` showing:

| Score | Demo value | Why judges care |
|---|---|---|
| GMP Score | 70.7/100 | Quantifies compliance — auditors love numbers |
| QMS Risk | 43/100 MEDIUM | ICH Q10 management review input |
| PV Risk | 100/100 CRITICAL | Links manufacturing → patient safety |
| ICH Q9 RPN | 12 MEDIUM | Standard pharma risk methodology |

**Say this:** *"Manual plants take 4–8 hours to detect deviations (PDA TR-59). PharmaOps detects in 30 seconds, investigates in 2.5 minutes, and auto-generates GMP + QMS + PV regulatory report — saving ₹5.2L per deviation and preventing ₹21L+ batch loss."*

## Web UI

```bash
streamlit run app/streamlit_app.py
```

## Splunk Dashboard

http://localhost:8000/en-US/app/search/pharmaops_monitor (set time: **All time**)

## Works Offline

If Splunk is unavailable, agents use local CSV data automatically.

## Key Files

| File | Purpose |
|---|---|
| `agent/multi_agent.py` | 3-agent system + regulatory scoring |
| `agent/regulatory_report.py` | GMP + QMS + PV unified report |
| `scripts/run_regulatory_demo.py` | One-command regulatory demo |
| `docs/INDUSTRY_IMPACT_STUDY.md` | Manual vs AI industry study |
| `agent/orchestrator.py` | Single-agent pipeline |
| `agent/splunk_mcp.py` | MCP → REST → CSV |
| `splunk/dashboards/pharmaops_monitor.xml` | Splunk dashboard |
| `splunk/alerts/pharma_anomaly_alert.spl` | Splunk alert |
