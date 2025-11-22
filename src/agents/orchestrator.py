"""
Pump Research Agent Orchestrator

Main script that coordinates the pump detection and investigation workflow.
This generates prompts for Claude Code to execute in headless mode.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.init import init_db, DB_PATH
from agents.pump_detector import get_detection_prompt, parse_pump_results, PUMP_THRESHOLD_PCT, TIME_WINDOW_MINUTES
from agents.news_investigator import get_investigation_prompt, parse_investigation_results
from agents.reporter import (
    save_pump_to_db, save_findings_to_db, save_trigger_to_db,
    get_telegram_report_prompt, save_notification_to_db,
    start_agent_run, complete_agent_run
)

ORCHESTRATOR_PROMPT = """
You are the Pump Research Agent orchestrator. Execute the following workflow:

## Phase 1: Initialize
- Ensure database is initialized at {db_path}

## Phase 2: Detect Pumps
{detection_prompt}

## Phase 3: Investigate Each Pump
For each detected pump, investigate using all available sources:
- Reddit MCP
- Twitter MCP
- Discord MCP
- Telegram MCP
- Web Search
- Grok MCP

## Phase 4: Report Findings
For each investigated pump:
1. Save pump data to SQLite database
2. Save all findings to database
3. Save identified trigger to database
4. Send summary to Telegram

## Execution Instructions

Execute each phase sequentially. After completing all phases, return a final summary:

```json
{{
  "run_id": <run_id>,
  "pumps_detected": <count>,
  "pumps_investigated": <count>,
  "total_findings": <count>,
  "notifications_sent": <count>,
  "errors": []
}}
```

Begin execution now.
"""

def generate_full_prompt(threshold_pct: float = None, time_window_minutes: int = None) -> str:
    """
    Generate the complete orchestrator prompt for Claude Code.

    Args:
        threshold_pct: Minimum price change percentage to detect
        time_window_minutes: Time window for detection in minutes
    """
    return ORCHESTRATOR_PROMPT.format(
        db_path=DB_PATH,
        detection_prompt=get_detection_prompt(threshold_pct, time_window_minutes)
    )

def main():
    """Main entry point - prints the orchestrator prompt."""
    parser = argparse.ArgumentParser(description="Pump Research Agent Orchestrator")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help=f"Minimum price change %% to detect (default: {PUMP_THRESHOLD_PCT})"
    )
    parser.add_argument(
        "--window",
        type=int,
        default=None,
        help=f"Time window in minutes (default: {TIME_WINDOW_MINUTES})"
    )
    args = parser.parse_args()

    # Initialize database
    init_db()

    # Generate and print the full prompt
    prompt = generate_full_prompt(args.threshold, args.window)
    print(prompt)

if __name__ == "__main__":
    main()
