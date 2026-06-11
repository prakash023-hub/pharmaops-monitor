#!/bin/bash
set -e
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true

echo "============================================"
echo "  PharmaOps Splunk Verification"
echo "============================================"

python3 << 'PYEOF'
import sys
sys.path.insert(0, "agent")
from splunk_mcp import search

checks = [
    ("Total events", "index=pharma_manufacturing | stats count", "count", 2000),
    ("DEVIATION events", "index=pharma_manufacturing sourcetype=temperature_logs.csv _raw=*DEVIATION* | stats count", "count", 100),
    ("BATCH-1027 deviations", "index=pharma_manufacturing _raw=*BATCH-1027* _raw=*DEVIATION* | stats count", "count", 20),
    ("FAIL batches", "index=pharma_manufacturing sourcetype=batch_summary.csv _raw=*FAIL* | stats count", "count", 5),
    ("Table query top count", "index=pharma_manufacturing sourcetype=temperature_logs.csv _raw=*DEVIATION* | rex field=_raw \"^(?<timestamp>[^,]+),(?<batch_id>[^,]+),(?<equipment_id>[^,]+),(?<product>[^,]+),(?<temperature_C>[^,]+),(?<status>[^,]+)\" | search batch_id=BATCH-* | stats count by batch_id | sort -count | head 1", "count", 24),
    ("Timechart", "index=pharma_manufacturing sourcetype=temperature_logs.csv | rex field=_raw \"^(?<timestamp>[^,]+),(?<batch_id>[^,]+),(?<equipment_id>[^,]+),(?<product>[^,]+),(?<temperature_C>[^,]+),(?<status>[^,]+)\" | search batch_id=BATCH-* | eval _time=strptime(timestamp, \"%Y-%m-%dT%H:%M:%S\"), temperature_C=tonumber(temperature_C) | timechart span=1h avg(temperature_C) as temperature | head 1", "_time", None),
]

all_ok = True
for label, q, field, expected in checks:
    r = search(q, earliest="0", latest="now")
    rows = r.get("rows", [])
    err = r.get("error", "")
    if err or not rows:
        print(f"  FAIL  {label}: {err or 'no rows'}")
        all_ok = False
        continue
    val = rows[0].get(field, "")
    if expected is not None:
        if field == "count" and int(val) >= int(expected):
            print(f"  OK    {label}: {val}")
        elif str(val) == str(expected):
            print(f"  OK    {label}: {val}")
        else:
            print(f"  FAIL  {label}: got {val}, expected >={expected}" if field == "count" else f"  FAIL  {label}: got {val}, expected {expected}")
            all_ok = False
    else:
        print(f"  OK    {label}: {rows[0]}")

if not all_ok:
    print("\n  Run: ./scripts/splunk_full_setup.sh")
    sys.exit(1)
print("\n  All checks passed!")
print("  Dashboard: http://localhost:8000/en-US/app/search/pharmaops_monitor")
PYEOF
echo "============================================"
