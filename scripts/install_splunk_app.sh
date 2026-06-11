#!/bin/bash
# Install PharmaOps Splunk app (props.conf) + dashboards
set -e
SPLUNK_HOME="${SPLUNK_HOME:-/Applications/Splunk}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
APP_DST="$SPLUNK_HOME/etc/apps/pharmaops_monitor"
VIEWS_USER="$SPLUNK_HOME/etc/users/admin/search/local/data/ui/views"
VIEWS_APP="$SPLUNK_HOME/etc/apps/search/local/data/ui/views"

if [ ! -d "$SPLUNK_HOME" ]; then
  echo "ERROR: Splunk not found at $SPLUNK_HOME"
  exit 1
fi

echo "[1/3] Installing PharmaOps Splunk app (CSV field extraction)..."
rm -rf "$APP_DST"
mkdir -p "$APP_DST/default"
cp "$REPO/splunk/app/default/app.conf" "$APP_DST/default/"
cp "$REPO/splunk/app/default/props.conf" "$APP_DST/default/"
cp "$REPO/splunk/app/default/transforms.conf" "$APP_DST/default/"

echo "[2/3] Installing dashboards..."
mkdir -p "$VIEWS_USER" "$VIEWS_APP"
cp "$REPO/splunk/dashboards/pharmaops_monitor.xml" "$VIEWS_USER/"
cp "$REPO/splunk/dashboards/pharmaops_classic.xml" "$VIEWS_USER/"
cp "$REPO/splunk/dashboards/pharmaops_classic.xml" "$VIEWS_APP/"

echo "[3/3] Done."
echo "  App:     $APP_DST"
echo "  Studio:  http://localhost:8000/en-US/app/search/pharmaops_monitor"
echo "  Classic: http://localhost:8000/en-US/app/search/pharmaops_classic"
echo ""
echo "  NEXT: /Applications/Splunk/bin/splunk restart"
echo "  THEN: ./scripts/refresh_splunk_data.sh"
