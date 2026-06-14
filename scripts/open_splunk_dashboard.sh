#!/bin/bash
# Open Splunk dashboard for video recording (run BEFORE multi-agent command)
open "http://localhost:8000/en-US/app/search/pharmaops_monitor"
echo "Splunk dashboard opened."
echo "Set time range to: All time"
echo ""
echo "Then run:"
echo "  python3 agent/pharma_agent.py --multi-agent --open-report"
