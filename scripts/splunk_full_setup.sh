#!/bin/bash
# Complete Splunk setup: app + restart + data + dashboards + verify
set -e
cd "$(dirname "$0")/.."
SPLUNK_HOME="${SPLUNK_HOME:-/Applications/Splunk}"

echo "============================================"
echo "  PharmaOps — Full Splunk Setup"
echo "============================================"

chmod +x scripts/install_splunk_app.sh scripts/refresh_splunk_data.sh scripts/verify_splunk.sh

echo "[1/5] Generate data..."
python3 generate_pharma_data.py

echo "[2/5] Install Splunk app + dashboards..."
./scripts/install_splunk_app.sh

echo "[3/5] Restart Splunk (required for props.conf)..."
"$SPLUNK_HOME/bin/splunk" restart
echo "  Waiting 30s for Splunk to start..."
sleep 30

echo "[4/5] Refresh index data..."
./scripts/refresh_splunk_data.sh

echo "  Waiting 20s for indexing to complete..."
sleep 20

echo "[5/5] Re-install dashboards + verify..."
./scripts/install_splunk_app.sh
./scripts/verify_splunk.sh

echo ""
echo "============================================"
echo "  OPEN: http://localhost:8000/en-US/app/search/pharmaops_monitor"
echo "  Time range: All time"
echo "============================================"
