#!/usr/bin/env python3
"""
PharmaOps Natural Language Interface

Gemini generates Splunk SPL from plain-English questions; all queries run
through Splunk MCP Server (with CSV fallback for offline demos).

Usage:
  python3 mcp_chat_demo.py                          # run 4 demo questions
  python3 mcp_chat_demo.py "What batches failed?"   # single question
  python3 mcp_chat_demo.py --interactive            # REPL mode
"""

import argparse
import json
import os
import re
import sys

from google import genai

from config import GEMINI_MODEL, SPLUNK_INDEX
from splunk_mcp import search

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SPL_SCHEMA = """
Index: pharma_manufacturing

Sources and fields:
- temperature_logs.csv: timestamp, batch_id, equipment_id, product, temperature_C, status (NORMAL|DEVIATION)
- moisture_logs.csv: timestamp, batch_id, equipment_id, product, moisture_pct, status (NORMAL|DEVIATION)
- batch_summary.csv: timestamp, batch_id, product, yield_pct, deviation_count, batch_status (PASS|FAIL), oee_score
- equipment_downtime.csv: timestamp, equipment_id, downtime_minutes, reason, severity
"""

DEMO_QUESTIONS = [
    "What batches failed and why?",
    "Which equipment had the most downtime?",
    "Show temperature deviations by batch",
    "Generate a GMP summary for the QA team",
]


def generate_spl(question: str) -> str:
    prompt = f"""You are a Splunk SPL expert for pharmaceutical manufacturing.

{SPL_SCHEMA}

User question: {question}

Write ONE Splunk search query to answer this question.
Rules:
- Must start with: search index={SPLUNK_INDEX}
- Use only fields listed above
- Return at most 20 results (use head 20)
- Output ONLY the SPL query, no explanation, no markdown, no backticks"""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    spl = response.text.strip()
    spl = re.sub(r"^```\w*\n?", "", spl)
    spl = re.sub(r"\n?```$", "", spl)
    spl = spl.strip().strip('"').strip("'")

    if not spl.lower().startswith("search"):
        spl = f"search index={SPLUNK_INDEX} {spl}"

    return spl


def chat(question: str) -> str:
    print(f"\n{'─'*60}")
    print(f"Plant Manager: {question}")

    print("  [Gemini] Generating SPL query...")
    spl = generate_spl(question)
    print(f"  [SPL]    {spl}")

    print("  [MCP]    Querying Splunk...")
    result = search(spl)
    rows = result.get("rows", [])
    source = result.get("source", "unknown")

    if result.get("error") and not rows:
        answer = f"Unable to query Splunk: {result['error']}"
        print(f"PharmaOps Agent: {answer}")
        return answer

    data_preview = json.dumps(rows[:10], default=str)
    if result.get("warning"):
        data_preview = json.dumps({"warning": result["warning"], "rows": rows[:10]}, default=str)

    answer_prompt = f"""You are PharmaOps AI assistant for a pharmaceutical plant manager.

Question: {question}
Data source: Splunk MCP ({source})
Splunk results: {data_preview}

Answer in 3-5 clear sentences. Cite specific batch IDs, equipment IDs, and numbers from the data.
If data is empty, say so honestly."""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=answer_prompt)
    answer = response.text.strip()
    print(f"PharmaOps Agent: {answer}")
    print(f"  [Source: {source} | {len(rows)} rows]")
    return answer


def interactive():
    print("=" * 60)
    print("  PharmaOps MCP Chat — Interactive Mode")
    print("  Type 'quit' to exit")
    print("=" * 60)
    while True:
        try:
            q = input("\nPlant Manager: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q or q.lower() in ("quit", "exit", "q"):
            break
        chat(q)


def main():
    parser = argparse.ArgumentParser(description="PharmaOps MCP Natural Language Chat")
    parser.add_argument("question", nargs="*", help="Question to ask")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive REPL")
    args = parser.parse_args()

    if not os.getenv("GEMINI_API_KEY"):
        print("[ERROR] Set GEMINI_API_KEY environment variable.")
        sys.exit(1)

    print("=" * 60)
    print("  PharmaOps MCP Chat — Natural Language Interface")
    print("  Gemini generates SPL → Splunk MCP executes → AI answers")
    print("=" * 60)

    if args.interactive:
        interactive()
    elif args.question:
        chat(" ".join(args.question))
    else:
        for q in DEMO_QUESTIONS:
            chat(q)


if __name__ == "__main__":
    main()
