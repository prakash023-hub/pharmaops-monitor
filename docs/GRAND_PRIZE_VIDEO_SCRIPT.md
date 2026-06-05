# Grand Prize Demo Video Script (under 3 minutes)

Record with **QuickTime → New Screen Recording** on your MacBook. No copyrighted music.

---

## Pre-recording checklist

- [ ] Splunk Enterprise running (`https://localhost:8000`)
- [ ] `pharma_manufacturing` index has data loaded
- [ ] Splunk MCP Server enabled and token in `~/mcp_token.txt`
- [ ] `export GEMINI_API_KEY=your_key`
- [ ] Terminal font size 14+ (readable on video)
- [ ] Close unrelated windows/notifications

---

## Scene-by-scene script

### 0:00 – 0:25 | THE PROBLEM

**Show:** Title slide or speak to camera.

**Say:**
> "Indian pharma exports 25 billion dollars annually. A single batch failure costs 50 to 150 lakh rupees. The FDA issues over 500 warning letters every year for inadequate process monitoring. Plant managers have no real-time AI view of GMP deviations — until now."

---

### 0:25 – 0:55 | SPLUNK DASHBOARD + AI DETECTION

**Show:** Splunk PharmaOps Monitor dashboard (all 5 panels). If Splunk unavailable, show `docs/dashboard/00_dashboard_overview.png`.

**Say:**
> "PharmaOps Monitor ingests manufacturing data into Splunk — temperature, moisture, batch QC, and equipment downtime. Splunk AI Toolkit uses Median Absolute Deviation to detect anomalies in real time. Here you can see temperature deviations by batch, AI anomaly bounds, GMP spec monitoring, pass-fail status, and equipment downtime."

**Point at:** BATCH-1011 or highest deviation batch on the deviations table.

---

### 0:55 – 1:35 | AUTONOMOUS AGENT (most important scene)

**Show:** Terminal — run from repo root:

```bash
cd ~/pharmaops-monitor
export GEMINI_API_KEY=your_key
python3 agent/pharma_agent.py --autonomous --open-report
```

**Say while it runs:**
> "When an anomaly is detected, our autonomous GMP investigator takes over. Watch — the agent queries Splunk through the MCP Server, gathers temperature, batch QC, and downtime evidence, reasons with Google Gemini, and generates an FDA-compliant deviation report. No human investigator required."

**Show:** HTML report opening in browser with GMP Impact badge and CAPA.

---

### 1:35 – 2:05 | NATURAL LANGUAGE CHAT

**Show:** Terminal:

```bash
python3 agent/mcp_chat_demo.py "What batches failed and why?"
python3 agent/mcp_chat_demo.py "Which equipment had the most downtime?"
```

**Say:**
> "Plant managers can ask questions in plain English. Gemini generates the Splunk query, MCP executes it on live data, and the agent answers with specific batch IDs and numbers."

---

### 2:05 – 2:40 | ARCHITECTURE + VALUE

**Show:** `architecture_diagram.png` from repo (open in Preview or show in README).

**Say:**
> "The architecture is simple: Splunk ingests manufacturing data, AI Toolkit detects anomalies, MCP Server gives agents secure access to Splunk, and Gemini provides reasoning and report generation. PharmaOps Monitor prevents batch failures worth lakhs of rupees — autonomously."

---

### 2:40 – 2:55 | CLOSE

**Show:** GitHub repo or HTML report.

**Say:**
> "PharmaOps Monitor — AI agents on Splunk for GMP compliance. Open source at github.com/prakash023-hub/pharmaops-monitor. Splunk Agentic Ops Hackathon 2026, Observability track."

---

## Upload

1. Upload to **YouTube** (public or unlisted)
2. Title: `PharmaOps Monitor — Autonomous GMP AI Agent on Splunk`
3. Description: link to GitHub repo
4. Paste YouTube URL into Devpost submission

---

## Common mistakes to avoid

- Video over 3 minutes (judges may stop watching)
- Only showing hardcoded batches — always use `--autonomous`
- Skipping the HTML report browser view
- Forgetting to mention Splunk MCP and AI Toolkit by name
