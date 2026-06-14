#!/usr/bin/env python3
"""Enable Splunk MCP built-in tools (run_query) via admin REST."""

import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

SPLUNK_REST = "https://localhost:8089"
USER = os.getenv("SPLUNK_USER", "admin")
PASS = os.getenv("SPLUNK_PASS", "Splunk@23")
MCP_TOOLS = f"{SPLUNK_REST}/servicesNS/nobody/Splunk_MCP_Server/mcp_tools"

TOOLS = [
    {"tool_id": "splunk_mcp_app_builtin:run_query", "tool_name": "run_query"},
]


def _ctx():
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


def _login():
    data = urllib.parse.urlencode({"username": USER, "password": PASS}).encode()
    req = urllib.request.Request(f"{SPLUNK_REST}/services/auth/login", data=data)
    resp = urllib.request.urlopen(req, context=_ctx(), timeout=15)
    return ET.parse(resp).find(".//sessionKey").text


def _api(session_key: str, method: str, query: dict | None = None, body: dict | None = None) -> dict:
    url = MCP_TOOLS
    if query:
        url += "?" + urllib.parse.urlencode({**query, "output_mode": "json"})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Splunk {session_key}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        resp = urllib.request.urlopen(req, context=_ctx(), timeout=30)
        raw = resp.read()
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"message": raw[:300]}
        parsed["error"] = exc.code
        return parsed


def _list_enabled(session_key: str) -> list[dict]:
    r = _api(session_key, "GET", query={"enabled_tools": "1"})
    return r.get("enabled_tools", [])


def _enable(session_key: str, tool_id: str, tool_name: str, override: bool = True) -> dict:
    return _api(
        session_key,
        "POST",
        body={
            "tool_id": tool_id,
            "tool_name": tool_name,
            "enabled": True,
            "override": override,
        },
    )


def main():
    print("Enabling Splunk MCP tools...")
    key = _login()

    enabled = _list_enabled(key)
    enabled_names = {t.get("tool_name") for t in enabled}
    print(f"  Currently enabled: {sorted(enabled_names) or '(none)'}")

    ok = 0
    for t in TOOLS:
        name = t["tool_name"]
        if name in enabled_names or (name == "run_query" and "splunk_run_query" in enabled_names):
            print(f"  OK  {name} (already enabled)")
            ok += 1
            continue

        r = _enable(key, t["tool_id"], name, override=True)
        if r.get("enabled") or "successfully" in r.get("message", "").lower():
            print(f"  OK  {name}")
            ok += 1
        elif r.get("error") == 409 and name in str(r):
            # Collision with built-in registry — enable via Splunk UI if this persists
            print(f"  WARN {name}: collision — open Splunk → MCP Server → Tools → enable {name}")
        else:
            print(f"  FAIL {name}: {r}")

    enabled = _list_enabled(key)
    if any(t.get("tool_name") in ("run_query", "splunk_run_query") for t in enabled):
        print("\nrun_query is enabled. Re-run: python3 agent/pharma_agent.py --health")
        return

    print("\nIf MCP still yellow, enable manually in Splunk UI:")
    print("  http://localhost:8000/en-US/app/Splunk_MCP_Server/tools")
    print("  → find 'run_query' → Enable (use override if prompted)")
    sys.exit(1 if ok == 0 else 0)


if __name__ == "__main__":
    main()
