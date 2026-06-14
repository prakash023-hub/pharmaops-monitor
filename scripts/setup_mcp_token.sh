#!/bin/bash
# Save Splunk MCP token — run once after generating token in Splunk MCP Server app
set -e
TOKEN_FILE="${SPLUNK_MCP_TOKEN_FILE:-$HOME/mcp_token.txt}"

echo "============================================"
echo "  PharmaOps — Setup Splunk MCP Token"
echo "============================================"
echo ""
echo "1. Open Splunk: http://localhost:8000"
echo "2. Go to: Splunk MCP Server app (left sidebar)"
echo "3. Enable MCP Server if not already on"
echo "4. Click 'Generate Token' → copy the token"
echo "5. Copy the MCP endpoint URL shown in the app"
echo ""
read -r -p "Paste MCP token here: " TOKEN
if [ -z "$TOKEN" ]; then
  echo "ERROR: No token entered"
  exit 1
fi
echo "$TOKEN" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"
echo ""
echo "Token saved to: $TOKEN_FILE"
echo ""
read -r -p "MCP endpoint URL [https://localhost:8089/services/mcp]: " MCP_URL
MCP_URL="${MCP_URL:-https://localhost:8089/services/mcp}"
echo ""
echo "Add to your shell before running demos:"
echo "  export SPLUNK_MCP_URL=\"$MCP_URL\""
echo ""
echo "Enable MCP tools + test:"
echo "  cd $(dirname "$0")/.. && source .venv/bin/activate"
echo "  python3 scripts/enable_mcp_tools.py"
echo "  python3 agent/pharma_agent.py --health"
