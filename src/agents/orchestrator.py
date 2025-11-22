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

## Phase 1: Detect Pumps
{detection_prompt}

## Phase 2: Investigate Each Pump
For each detected pump, investigate using all available sources:
- Reddit MCP: Search for posts about the token
- Twitter MCP: Search for tweets and announcements
- Discord MCP: Check crypto servers for mentions
- Web Search: Look for news articles and announcements
- Grok MCP: Get AI analysis of the pump

## Phase 3: Save to Database
For each pump and its findings, execute Python code to save to SQLite at {db_path}:

```python
import sqlite3
conn = sqlite3.connect('{db_path}')

# Save pump
cursor = conn.execute('''
    INSERT INTO pumps (symbol, price_change_pct, time_window_minutes, price_at_detection, volume_change_pct, market_cap, source)
    VALUES (?, ?, ?, ?, ?, ?, ?)
''', (symbol, price_change_pct, time_window_minutes, price_at_detection, volume_change_pct, market_cap, source))
pump_id = cursor.lastrowid

# Save findings
for finding in findings:
    conn.execute('''
        INSERT INTO findings (pump_id, source_type, source_url, content, relevance_score, sentiment)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (pump_id, finding['source_type'], finding.get('source_url'), finding['content'], finding.get('relevance_score'), finding.get('sentiment')))

# Save trigger
conn.execute('''
    INSERT INTO news_triggers (pump_id, trigger_type, description, confidence)
    VALUES (?, ?, ?, ?)
''', (pump_id, trigger_type, description, confidence))

conn.commit()
conn.close()
```

## Phase 4: Send Telegram Alert
For each pump, use the Telegram MCP to send a message with this format:

🚀 **PUMP DETECTED: ${{symbol}}**

📈 Price: +{{price_change_pct}}% ({{time_window}} min)
💰 Current: ${{price}}

🔍 **Trigger:** {{trigger_type}}
{{description}}

**Key Findings:**
- {{finding_1}}
- {{finding_2}}
- {{finding_3}}

Send to the chat configured in TELEGRAM_CHAT_ID.

## Execution

Execute all phases. If no pumps detected, skip phases 2-4.

Return summary:
```json
{{
  "pumps_detected": <count>,
  "findings_count": <count>,
  "notifications_sent": <count>
}}
```
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
