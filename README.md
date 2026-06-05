# PharmaOps Monitor

> AI agents on Splunk that detect GMP deviations, investigate root causes autonomously, and generate FDA-compliant reports — preventing ₹50L+ batch failures in real time.

[![Splunk Agentic Ops Hackathon 2026](https://img.shields.io/badge/Hackathon-Splunk%20Agentic%20Ops%202026-blue)](https://splunk.devpost.com/)
[![Track](https://img.shields.io/badge/Track-Observability-green)](https://splunk.devpost.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

![Dashboard Overview](docs/dashboard/00_dashboard_overview.png)

## Problem

India exports **$25B in pharma** annually. Batch failures cost **₹50–150 lakhs** each. The FDA issues **500+ warning letters/year** for inadequate monitoring. Plant managers have no real-time AI view of GMP deviations.

## Solution

PharmaOps Monitor ingests pharma manufacturing data into Splunk, uses **Splunk AI Toolkit** for anomaly detection, and deploys **autonomous AI agents** via **Splunk MCP Server** to investigate deviations and generate FDA-compliant CAPA reports — without human intervention.

## Architecture

![Architecture](architecture_diagram.png)

```
Manufacturing Data → Splunk Index → AI Toolkit (MAD anomalies)
                                        ↓
                              Splunk MCP Server
                                        ↓
                    Python Agents + Google Gemini
                                        ↓
                         FDA HTML Deviation Reports
```

## Features

| Feature | Technology |
|---|---|
| AI temperature anomaly detection | Splunk AI Toolkit + MAD algorithm |
| GMP dashboard (5 panels) | Splunk Enterprise |
| Autonomous GMP investigator | Splunk MCP + Gemini 2.5-flash |
| Natural language plant manager chat | Gemini generates SPL → MCP executes |
| FDA-style deviation reports | Auto-generated HTML reports |

## Quick Demo (5 minutes)

### Prerequisites

- Splunk Enterprise 10.4.0 (with Developer License)
- Splunk AI Toolkit 5.7.4
- Splunk MCP Server 1.2.0
- Python 3.12+
- Google Gemini API key

### 1. Clone and install

```bash
git clone https://github.com/prakash023-hub/pharmaops-monitor.git
cd pharmaops-monitor
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GEMINI_API_KEY
export GEMINI_API_KEY=your_key_here
```

### 2. Load data into Splunk

```bash
python3 generate_pharma_data.py
# Upload CSVs to index: pharma_manufacturing
# (temperature_logs.csv, moisture_logs.csv, batch_summary.csv, equipment_downtime.csv)
```

### 3. Configure Splunk MCP

```bash
# Save your MCP bearer token:
echo "your_mcp_token" > ~/mcp_token.txt
# Or: export SPLUNK_MCP_TOKEN=your_mcp_token
```

### 4. Run autonomous agent (Grand Prize demo)

```bash
./run_demo.sh
# Or step by step:
python3 agent/pharma_agent.py --autonomous --open-report
```

This will:
1. **Detect** the batch with most temperature deviations (via Splunk MCP)
2. **Investigate** — query temperature, QC, downtime, moisture evidence
3. **Reason** with Gemini LLM
4. **Generate** JSON + FDA HTML deviation report (opens in browser)

### 5. Natural language chat

```bash
python3 agent/mcp_chat_demo.py                              # 4 demo questions
python3 agent/mcp_chat_demo.py "What batches failed?"       # single question
python3 agent/mcp_chat_demo.py --interactive                # REPL mode
```

### 6. Regenerate dashboard previews (optional)

```bash
python3 scripts/generate_dashboard_previews.py
```

## Agent Commands

| Command | Description |
|---|---|
| `python3 agent/pharma_agent.py --autonomous` | Detect + investigate top anomaly |
| `python3 agent/pharma_agent.py --demo` | Investigate top 2 anomalies |
| `python3 agent/pharma_agent.py --batch BATCH-1011` | Investigate specific batch |
| `python3 agent/pharma_agent.py --autonomous --open-report` | Auto-open HTML report |
| `python3 agent/generate_report_html.py agent/reports/report_BATCH-1011.json` | JSON → HTML |
| `python3 agent/mcp_chat_demo.py --interactive` | Chat REPL |

## Dashboard Panels

| Panel | File |
|---|---|
| Temperature Deviations by Batch | [docs/dashboard/01_temperature_deviations_by_batch.png](docs/dashboard/01_temperature_deviations_by_batch.png) |
| AI Temperature Anomaly Detection | [docs/dashboard/02_ai_anomaly_detection.png](docs/dashboard/02_ai_anomaly_detection.png) |
| GMP Temperature Monitoring | [docs/dashboard/03_gmp_temperature_bounds.png](docs/dashboard/03_gmp_temperature_bounds.png) |
| Batch Pass/Fail Status | [docs/dashboard/04_batch_pass_fail.png](docs/dashboard/04_batch_pass_fail.png) |
| Equipment Downtime | [docs/dashboard/05_equipment_downtime.png](docs/dashboard/05_equipment_downtime.png) |

## Data

| File | Rows | Description |
|---|---|---|
| temperature_logs.csv | 1,800 | Coating machine temp every 5 min |
| moisture_logs.csv | 600 | Granulation moisture every 10 min |
| batch_summary.csv | 50 | Batch yield, OEE, pass/fail |
| equipment_downtime.csv | 23 | Downtime events with severity |
| **Total** | **2,473** | `pharma_manufacturing` index |

## Splunk Queries

Saved in `splunk/` directory:

- `anomaly_detection.spl` — MAD-based AI anomaly bounds
- `deviation_by_batch.spl` — Temperature deviations by batch
- `batch_quality.spl` — Pass/fail batch status
- `equipment_downtime.spl` — Downtime by machine
- `moisture_anomaly.spl` — Moisture deviation detection

## Project Structure

```
pharmaops-monitor/
├── agent/
│   ├── pharma_agent.py          # Autonomous GMP investigator
│   ├── mcp_chat_demo.py         # Natural language interface
│   ├── splunk_mcp.py            # Splunk MCP client + CSV fallback
│   ├── generate_report_html.py  # FDA HTML report generator
│   └── reports/                 # Generated JSON + HTML reports
├── splunk/                      # Saved SPL queries
├── scripts/
│   └── generate_dashboard_previews.py
├── docs/
│   ├── dashboard/               # Dashboard screenshots
│   ├── GRAND_PRIZE_VIDEO_SCRIPT.md
│   └── DEVPOST_SUBMISSION.md
├── architecture_diagram.png
└── requirements.txt
```

## Hackathon Submission

- **Track:** Observability
- **Bonus prizes:** Best Use of Splunk MCP Server, Best Use of Splunk Hosted Models
- **Video script:** [docs/GRAND_PRIZE_VIDEO_SCRIPT.md](docs/GRAND_PRIZE_VIDEO_SCRIPT.md)
- **Devpost copy:** [docs/DEVPOST_SUBMISSION.md](docs/DEVPOST_SUBMISSION.md)

## Author

**Prakash Raj K** — Associate Professor, Sri Balaji Vidyapeeth, Puducherry, India

## License

MIT — see [LICENSE](LICENSE)
