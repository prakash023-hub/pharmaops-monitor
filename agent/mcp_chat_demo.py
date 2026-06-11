#!/usr/bin/env python3
"""
PharmaOps Natural Language Interface

Gemini generates Splunk SPL from plain-English questions; queries run
through Splunk MCP → REST → CSV fallback.

Usage:
  python3 mcp_chat_demo.py
  python3 mcp_chat_demo.py "What batches failed?"
  python3 mcp_chat_demo.py --interactive
"""

import argparse
import json
import os
import re
import sys

from google import genai

from config import GEMINI_MODEL, SPLUNK_INDEX
from splunk_mcp import SPL_TEMPLATES, search

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SPL_SCHEMA = f"""
Index: {SPLUNK_INDEX}

IMPORTANT: CSV data is stored as raw text. Use these working query patterns:

Failed batches:
{SPL_TEMPLATES['failed_batches']}

Deviations by batch:
{SPL_TEMPLATES['deviations_by_batch']}

Equipment downtime:
{SPL_TEMPLATES['equipment_downtime']}

Always use sourcetype= not source=, and use rex to extract fields from _raw when needed.
"""

DEMO_QUESTIONS = [
    "What batches failed and why?",
    "Which equipment had the most downtime?",
    "Show temperature deviations by batch",
    "Generate a GMP summary for the QA team",
]


def generate_spl(question: str) -> str:
    canned = None
    q = question.lower()
    if any(w in q for w in ("fail", "failed")):
        canned = SPL_TEMPLATES["failed_batches"]
    elif "downtime" in q or "equipment" in q:
        canned = SPL_TEMPLATES["equipment_downtime"]
    elif "deviation" in q or "temperature" in q:
        canned = SPL_TEMPLATES["deviations_by_batch"]

    if canned:
        return canned

    prompt = f"""You are a Splunk SPL expert for pharmaceutical manufacturing.

{SPL_SCHEMA}

User question: {question}

Write ONE Splunk search query. Use the working patterns above.
Output ONLY the SPL query, no markdown."""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    spl = response.text.strip()
    spl = re.sub(r"^```\w*\n?", "", spl)
    spl = re.sub(r"\n?```$", "", spl)
    spl = spl.strip().strip('"').strip("'")
    if not spl.lower().startswith("search"):
        spl = f"search index={SPLUNK_INDEX} {spl}"
    return spl


def ask(question: str, verbose: bool = False) -> dict:
    """Answer a plant manager question. Returns dict for Streamlit or CLI."""
    if verbose:
        print(f"\n{'─'*60}\nPlant Manager: {question}")

    spl = generate_spl(question)
    if verbose:
        print(f"  [SPL] {spl}")

    result = search(spl, question=question)
    rows = result.get("rows", [])
    source = result.get("source", "unknown")
    spl_used = result.get("spl_used", spl)

    if result.get("error") and not rows:
        answer = f"Unable to query data: {result['error']}"
        if verbose:
            print(f"PharmaOps Agent: {answer}")
        return {"answer": answer, "spl": spl_used, "source": source, "rows": []}

    data_preview = json.dumps(rows[:10], default=str)
    answer_prompt = f"""You are PharmaOps AI assistant for a pharmaceutical plant manager.

Question: {question}
Data source: {source}
Splunk results: {data_preview}

Answer in 3-5 clear sentences. Cite specific batch IDs, products, deviation counts, and reasons.
For BATCH-1027 mention coating thermostat drift if in data."""

    response = client.models.generate_content(model=GEMINI_MODEL, contents=answer_prompt)
    answer = response.text.strip()

    if verbose:
        print(f"PharmaOps Agent: {answer}")
        print(f"  [Source: {source} | {len(rows)} rows]")

    return {"answer": answer, "spl": spl_used, "source": source, "rows": rows}


def chat(question: str) -> str:
    """CLI wrapper — prints progress and returns answer text."""
    print("  [Gemini] Generating SPL query...")
    return ask(question, verbose=True)["answer"]


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
    print("  Gemini SPL → Splunk REST/MCP → AI answer")
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
