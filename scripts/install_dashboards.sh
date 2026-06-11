#!/bin/bash
# Copy PharmaOps dashboards into Splunk and reload UI
set -e
SPLUNK_HOME="${SPLUNK_HOME:-/Applications/Splunk}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
VIEWS_USER="$SPLUNK_HOME/etc/users/admin/search/local/data/ui/views"
VIEWS_APP="$SPLUNK_HOME/etc/apps/search/local/data/ui/views"

mkdir -p "$VIEWS_USER" "$VIEWS_APP"
cp "$REPO/splunk/dashboards/pharmaops_classic.xml" "$VIEWS_USER/"
cp "$REPO/splunk/dashboards/pharmaops_classic.xml" "$VIEWS_APP/"
cp "$REPO/splunk/dashboards/pharmaops_monitor.xml" "$VIEWS_USER/"

echo "Dashboards installed:"
echo "  Classic: http://localhost:8000/en-US/app/search/pharmaops_classic"
echo "  Studio:  http://localhost:8000/en-US/app/search/pharmaops_monitor"
echo ""
echo "Reload Splunk UI (pick one):"
echo "  Option A: Settings -> Server settings -> General -> Reload Splunk"
echo "  Option B: /Applications/Splunk/bin/splunk restart"
echo ""
echo "On dashboard: set Time Range = All time"
