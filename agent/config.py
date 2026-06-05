import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
AGENT_DIR = Path(__file__).resolve().parent
REPORTS_DIR = AGENT_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

SPLUNK_MCP_URL = os.getenv("SPLUNK_MCP_URL", "https://localhost:8089/services/mcp")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
SPLUNK_INDEX = "pharma_manufacturing"

CSV_SOURCES = {
    "temperature_logs.csv": ROOT_DIR / "temperature_logs.csv",
    "moisture_logs.csv": ROOT_DIR / "moisture_logs.csv",
    "batch_summary.csv": ROOT_DIR / "batch_summary.csv",
    "equipment_downtime.csv": ROOT_DIR / "equipment_downtime.csv",
}


def load_mcp_token():
    token = os.getenv("SPLUNK_MCP_TOKEN")
    if token:
        return token.strip()
    token_path = Path(os.getenv("SPLUNK_MCP_TOKEN_FILE", Path.home() / "mcp_token.txt"))
    if token_path.exists():
        return token_path.read_text().strip()
    return None
