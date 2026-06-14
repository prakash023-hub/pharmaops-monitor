"""Environment helpers — separate module to avoid 'config' name conflicts in Streamlit."""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_env() -> None:
    """Load .env from project root (does not override existing env vars)."""
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def gemini_key_ok() -> bool:
    """True only if GEMINI_API_KEY looks like a real Google API key."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or len(key) < 30:
        return False
    placeholders = {
        "your_key",
        "your_key_here",
        "your_gemini_api_key_here",
        "paste_your_real_key_here",
        "your_actual_key",
        "your_actual_key_here",
    }
    if key.lower() in placeholders or key.startswith("your_"):
        return False
    return True


load_env()
