#!/bin/bash
# PharmaOps Monitor — Grand Prize demo runner
set -e
cd "$(dirname "$0")"

if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

if [ -z "$GEMINI_API_KEY" ]; then
  echo "ERROR: Set GEMINI_API_KEY first:"
  echo "  export GEMINI_API_KEY=your_key"
  exit 1
fi

echo "============================================"
echo "  PharmaOps Monitor — Grand Prize Demo"
echo "============================================"

echo ""
echo "[1/3] Autonomous GMP Investigator..."
python3 agent/pharma_agent.py --autonomous --open-report

echo ""
echo "[2/3] Natural Language Chat (4 demo questions)..."
python3 agent/mcp_chat_demo.py

echo ""
echo "[3/3] Demo complete!"
echo "  Reports: agent/reports/"
echo "  Video script: docs/GRAND_PRIZE_VIDEO_SCRIPT.md"
echo "  Devpost copy: docs/DEVPOST_SUBMISSION.md"
