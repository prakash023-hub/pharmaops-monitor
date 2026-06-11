#!/bin/bash
# Refresh Splunk index with latest CSV data (run AFTER install_splunk_app.sh + restart)
set -e
SPLUNK_HOME="${SPLUNK_HOME:-/Applications/Splunk}"
INDEX="pharma_manufacturing"
DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SPLUNK_USER="${SPLUNK_USER:-admin}"
SPLUNK_PASS="${SPLUNK_PASS:-Splunk@23}"
AUTH="${SPLUNK_USER}:${SPLUNK_PASS}"

echo "============================================"
echo "  PharmaOps — Refresh Splunk Data"
echo "============================================"

if [ ! -d "$SPLUNK_HOME" ]; then
  echo "ERROR: Splunk not found at $SPLUNK_HOME"
  exit 1
fi

if [ ! -d "$SPLUNK_HOME/etc/apps/pharmaops_monitor" ]; then
  echo "WARNING: PharmaOps app not installed. Run: ./scripts/install_splunk_app.sh"
fi

echo "[1/4] Removing old index..."
"$SPLUNK_HOME/bin/splunk" remove index "$INDEX" -auth "$AUTH" 2>/dev/null || true

echo "[2/4] Creating fresh index..."
"$SPLUNK_HOME/bin/splunk" add index "$INDEX" -auth "$AUTH"

echo "[3/4] Ingesting CSV files (with field extraction via props.conf)..."
for f in temperature_logs.csv moisture_logs.csv batch_summary.csv equipment_downtime.csv; do
  if [ ! -f "$DATA_DIR/$f" ]; then
    echo "ERROR: Missing $f — run: python3 generate_pharma_data.py"
    exit 1
  fi
  echo "  → $f"
  "$SPLUNK_HOME/bin/splunk" add oneshot "$DATA_DIR/$f" -index "$INDEX" -sourcetype "$f" -auth "$AUTH"
done

echo "[4/4] Waiting for indexing..."
sleep 3

echo ""
echo "============================================"
echo "  Done!"
echo "  Dashboard: http://localhost:8000/en-US/app/search/pharmaops_monitor"
echo "  Time range: All time"
echo "  Expected: BATCH-1027 deviation count = 24"
echo "============================================"
