#!/bin/bash
# Ingest pharma CSVs into Splunk index pharma_manufacturing
# Run after: python3 generate_pharma_data.py

set -e
SPLUNK_HOME="${SPLUNK_HOME:-/Applications/Splunk}"
INDEX="pharma_manufacturing"
DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Ingesting pharma data into Splunk index: $INDEX"
echo "Data directory: $DATA_DIR"

for f in temperature_logs.csv moisture_logs.csv batch_summary.csv equipment_downtime.csv; do
  if [ ! -f "$DATA_DIR/$f" ]; then
    echo "ERROR: Missing $f — run: python3 generate_pharma_data.py"
    exit 1
  fi
  echo "  → $f"
  "$SPLUNK_HOME/bin/splunk" add oneshot "$DATA_DIR/$f" -index "$INDEX" -sourcetype "$f" -auth admin:Splunk@23
done

echo ""
echo "Done. Verify in Splunk:"
echo "  index=$INDEX | stats count by source"
echo ""
echo "Open dashboard:"
echo "  http://localhost:8000/en-US/app/search/pharmaops_monitor"
