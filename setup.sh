#!/bin/bash
# PharmaOps Monitor — One-command judge setup
set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  PharmaOps Monitor — Judge Setup"
echo "============================================"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt

echo "[1/4] Generating manufacturing data..."
python3 generate_pharma_data.py

if [ -d "/Applications/Splunk" ]; then
  echo "[2/4] Full Splunk setup (app + restart + ingest + dashboards)..."
  chmod +x scripts/splunk_full_setup.sh scripts/install_splunk_app.sh scripts/refresh_splunk_data.sh scripts/verify_splunk.sh
  ./scripts/splunk_full_setup.sh
else
  echo "[2/4] Splunk not found — using local CSV data (works offline)"
  echo "[3/4] Dashboard XML in splunk/dashboards/"
fi

echo "[3/4] Generating dashboard previews..."
python3 scripts/generate_dashboard_previews.py

echo "[4/4] System health check..."
if [ -z "$GEMINI_API_KEY" ]; then
  echo "  Set GEMINI_API_KEY to run AI agents: export GEMINI_API_KEY=your_key"
else
  python3 agent/pharma_agent.py --health
fi

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  Dashboard: http://localhost:8000/en-US/app/search/pharmaops_monitor"
echo "  Demo:      ./run_demo.sh"
echo "  UI:        streamlit run app/streamlit_app.py"
echo "============================================"
