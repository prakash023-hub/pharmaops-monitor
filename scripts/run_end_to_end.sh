#!/bin/bash
# PharmaOps — complete end-to-end demo (all components)
set -e
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

if [ -z "$GEMINI_API_KEY" ]; then
  echo "ERROR: export GEMINI_API_KEY=your_key"
  exit 1
fi

echo "============================================"
echo "  PHARMAOPS END-TO-END DEMO"
echo "============================================"

echo ""
echo "[1/6] Health check..."
python3 agent/pharma_agent.py --health

echo ""
echo "[2/6] Splunk data verify..."
./scripts/verify_splunk.sh

echo ""
echo "[3/6] Regulatory report (GMP+QMS+PV)..."
python3 scripts/run_regulatory_demo.py

echo ""
echo "[4/6] Multi-agent investigation..."
python3 agent/pharma_agent.py --multi-agent --open-report

echo ""
echo "[5/6] Ask AI — failed batches..."
python3 agent/mcp_chat_demo.py "What batches failed and why?"

echo ""
echo "[6/6] Launch Streamlit UI..."
echo "  Starting Streamlit in a new step — run this in a NEW terminal tab:"
echo "    cd $(pwd) && source .venv/bin/activate && ./run_streamlit.sh"
echo ""
echo "  Or open manually: http://localhost:8501"
echo ""
echo "  Splunk dashboard:"
echo "  http://localhost:8000/en-US/app/search/pharmaops_monitor"
echo ""
echo "============================================"
echo "  END-TO-END DEMO COMPLETE"
echo "============================================"
