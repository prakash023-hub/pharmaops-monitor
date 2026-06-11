#!/bin/bash
# PharmaOps Monitor — Grand Prize demo (multi-agent)
set -e
cd "$(dirname "$0")"
[ -d ".venv" ] && source .venv/bin/activate

if [ -z "$GEMINI_API_KEY" ]; then
  echo "ERROR: export GEMINI_API_KEY=your_key"
  exit 1
fi

echo "============================================"
echo "  PharmaOps Monitor — MULTI-AGENT DEMO"
echo "  Detection → Investigation → QA Review"
echo "============================================"

echo ""
echo "[0] Health check..."
python3 agent/pharma_agent.py --health

echo ""
echo "[1] Multi-agent pipeline..."
python3 agent/pharma_agent.py --multi-agent --open-report

echo ""
echo "[2] Watchdog (auto-trigger simulation)..."
python3 agent/watchdog.py --once

echo ""
echo "[3] Natural language chat..."
python3 agent/mcp_chat_demo.py

echo ""
echo "[4] Launch web UI:"
echo "    streamlit run app/streamlit_app.py"
echo ""
echo "  Reports: agent/reports/"
echo "  Alerts:  agent/reports/alerts.jsonl"
