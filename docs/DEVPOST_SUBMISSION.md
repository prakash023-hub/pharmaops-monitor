# Devpost Submission — Copy & Paste Guide

Submit at: https://splunk.devpost.com/

---

## Project Name

```
PharmaOps Monitor
```

## Tagline (short description)

```
AI agents on Splunk that detect GMP deviations, investigate root causes autonomously, and generate FDA-compliant reports — preventing ₹50L+ batch failures in real time.
```

## Track

```
Observability
```

## Inspiration

Indian pharmaceutical manufacturing exports $25B annually, yet batch failures cost ₹50–150 lakhs each and FDA issues 500+ warning letters per year for inadequate process monitoring. Existing MES and SCADA systems alert operators but require manual investigation — taking hours while batches continue at risk. We built PharmaOps Monitor to give plant managers an autonomous AI investigator that never sleeps.

## What it does

PharmaOps Monitor is an end-to-end AI observability platform for pharmaceutical manufacturing:

1. **Splunk ingestion** — Temperature, moisture, batch QC, and equipment downtime data in the `pharma_manufacturing` index
2. **AI anomaly detection** — Splunk AI Toolkit with Median Absolute Deviation (MAD) catches temperature excursions in real time
3. **Autonomous GMP investigator** — When anomalies are detected, an AI agent queries Splunk via MCP Server, gathers multi-source evidence, reasons with Google Gemini, and generates structured deviation reports with root cause, GMP impact, CAPA, and financial impact
4. **Natural language interface** — Plant managers ask questions in plain English; Gemini generates SPL, MCP executes on live data, AI answers with specific batch IDs and numbers
5. **FDA + ICH compliant reports** — Maps every deviation to ICH Q7/Q8/Q9/Q10 + FDA 21 CFR Part 211 with Q9 Risk Priority Number (RPN)
6. **FDA-style HTML reports** — Professional deviation reports open in browser for QA review

## How we built it

- **Splunk Enterprise 10.4.0** — Data backbone with Developer License
- **Splunk AI Toolkit 5.7.4** — MAD-based anomaly detection on dashboard panels
- **Splunk MCP Server 1.2.0** — Secure agent access to Splunk search; all agent queries go through MCP
- **Google Gemini 2.5-flash** — LLM reasoning for investigation and NL-to-SPL translation
- **Python 3.12** — Agent orchestration (`pharma_agent.py`, `mcp_chat_demo.py`)
- **Synthetic pharma dataset** — 2,473 events across 4 CSV sources with injected anomalies

Architecture: Manufacturing CSVs → Splunk Index → AI Toolkit (anomaly detection) → MCP Server → Python Agents → Gemini → FDA HTML Reports

## Challenges we ran into

- Parsing Splunk MCP JSON-RPC responses required a robust extraction layer with CSV fallback for offline demos
- Getting Gemini to generate valid SPL from natural language required careful schema prompting
- Ensuring the autonomous agent truly detects anomalies (not hardcoded batch IDs) was critical for demonstrating agentic behavior

## Regulatory Framework

- **ICH Q7** — GMP for APIs (process controls, deviation handling)
- **ICH Q8** — Critical Quality Attributes (temperature, moisture as CQAs)
- **ICH Q9(R1)** — Quality Risk Management (RPN scoring for every deviation)
- **ICH Q10** — Pharmaceutical Quality System (CAPA, change control)
- **FDA 21 CFR Part 211** — US GMP requirements (§211.100, §211.192, §211.68)

## Accomplishments that we're proud of

- First autonomous GMP compliance agent built on Splunk MCP with ICH regulatory mapping
- Full detect → investigate → report loop with zero human input
- Natural language plant manager interface grounded in live Splunk data
- FDA-style HTML deviation reports generated automatically
- End-to-end demo in under 5 minutes from README instructions

## What we learned

- Splunk MCP Server is a powerful bridge between LLM agents and operational data
- Domain-specific observability (pharma GMP) creates more compelling impact stories than generic IT monitoring
- Combining Splunk AI Toolkit detection with external LLM reasoning gives the best of both platforms

## What's next for PharmaOps Monitor

- Real-time alert trigger: Splunk saved search → webhook → autonomous agent
- Splunk Cloud deployment for multi-site pharma plants
- Integration with LIMS and MES systems via HEC
- Multi-agent workflow: detection agent → investigation agent → QA approval agent

## Built with

```
Splunk Enterprise, Splunk AI Toolkit, Splunk MCP Server, Google Gemini, Python, pandas, matplotlib
```

## Links

| Field | Value |
|---|---|
| GitHub Repository | https://github.com/prakash023-hub/pharmaops-monitor |
| Demo Video | [Paste YouTube URL after recording] |
| Architecture Diagram | https://github.com/prakash023-hub/pharmaops-monitor/blob/main/architecture_diagram.png |

## Bonus prize eligibility

- **Best Use of Splunk MCP Server** — All agent queries use MCP; autonomous investigation workflow
- **Best Use of Splunk Hosted Models** — Splunk AI Toolkit MAD anomaly detection on dashboard

## Try it out instructions (for judges)

```bash
git clone https://github.com/prakash023-hub/pharmaops-monitor
cd pharmaops-monitor
pip install -r requirements.txt
export GEMINI_API_KEY=your_key
# With Splunk + MCP running:
python3 agent/pharma_agent.py --autonomous --open-report
python3 agent/mcp_chat_demo.py
```

Without Splunk, agents fall back to local CSV data for demonstration.
