#!/usr/bin/env python3
"""
PharmaOps CLI — End-to-End AI Agent

Usage:
  python3 pharma_agent.py --multi-agent --open-report   # 3-agent pipeline (recommended)
  python3 pharma_agent.py --autonomous --open-report      # single-agent pipeline
  python3 pharma_agent.py --health
  python3 pharma_agent.py --watchdog
"""

import argparse
import os
import sys

from orchestrator import check_system, investigate_batch, run_full_pipeline


def main():
    parser = argparse.ArgumentParser(description="PharmaOps End-to-End AI Agent")
    parser.add_argument("--multi-agent", action="store_true", help="3-agent pipeline (Detection→Investigation→QA)")
    parser.add_argument("--autonomous", action="store_true", help="Single-agent pipeline")
    parser.add_argument("--health", action="store_true", help="System health check")
    parser.add_argument("--watchdog", action="store_true", help="Auto-trigger on new anomaly")
    parser.add_argument("--batch", type=str, help="Investigate specific batch")
    parser.add_argument("--open-report", action="store_true", help="Open HTML report in browser")
    args = parser.parse_args()

    if args.health:
        h = check_system()
        print("PharmaOps System Health:")
        for k, v in h.items():
            print(f"  {k}: {v}")
        sys.exit(0 if h.get("ready") else 1)

    if not os.getenv("GEMINI_API_KEY"):
        print("[ERROR] Set GEMINI_API_KEY environment variable.")
        sys.exit(1)

    if args.watchdog:
        from watchdog import check_and_investigate
        check_and_investigate()
    elif args.multi_agent or (not args.autonomous and not args.batch):
        from multi_agent import run_multi_agent
        run_multi_agent(open_browser=args.open_report)
    elif args.batch:
        investigate_batch(args.batch, open_browser=args.open_report)
    else:
        run_full_pipeline(open_browser=args.open_report)


if __name__ == "__main__":
    main()
