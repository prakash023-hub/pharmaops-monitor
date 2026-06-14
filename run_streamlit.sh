#!/bin/bash
# Launch Streamlit using project venv (NOT anaconda)
set -e
cd "$(dirname "$0")"
PORT="${STREAMLIT_PORT:-8501}"
URL="http://localhost:${PORT}"

if [ ! -d ".venv" ]; then
  echo "Creating venv..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -q -r requirements.txt
else
  source .venv/bin/activate
fi

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
  echo "Loaded .env"
fi

if [ -z "$GEMINI_API_KEY" ] || [ "${#GEMINI_API_KEY}" -lt 30 ]; then
  echo "WARNING: GEMINI_API_KEY missing or invalid (need ~39 char key from aistudio.google.com/apikey)"
  echo "  Create .env file:  echo 'GEMINI_API_KEY=your_key' > .env"
  echo "  Or export:         export GEMINI_API_KEY=your_key"
fi

if lsof -i ":${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Streamlit already running on ${URL}"
  open "${URL}" 2>/dev/null || true
  echo "Opened browser. If nothing appears, paste this URL manually:"
  echo "  ${URL}"
  exit 0
fi

echo "Using: $(which python3)"
python3 -c "import numpy, pandas, streamlit; print('numpy', numpy.__version__, 'pandas', pandas.__version__, 'streamlit', streamlit.__version__)"

echo ""
echo "Starting PharmaOps Streamlit UI..."
echo "  URL: ${URL}"
echo "  (One browser tab opens in ~3 seconds. Keep this terminal open.)"
echo ""

# Single browser open (Streamlit headless=true in .streamlit/config.toml avoids double-open)
(sleep 3 && open "${URL}") &

exec python3 -m streamlit run app/streamlit_app.py --server.port "${PORT}" --server.headless true
