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
For each detected pump, you MUST search for the actual news/event that caused the pump. Use these MCP tools:

### Twitter/X (REQUIRED)
Use the Twitter MCP to search for:
- `${{symbol}} announcement` - official announcements
- `${{symbol}} news` - breaking news
- `${{symbol}} listing` - exchange listings
- `${{symbol}} partnership` - partnerships

Look for tweets from official accounts, crypto news outlets, or influencers.

### Reddit (REQUIRED)
Use the Reddit MCP to search r/cryptocurrency, r/CryptoMoonShots, r/altcoin for:
- Posts about the token in the last 24 hours
- Any news, partnerships, or announcements

### Web Search
Search for recent news articles about the token.

### What to Extract
For EACH source, extract:
- **content**: The actual news/tweet/post text (not just "search performed")
- **source_url**: Direct link to the tweet/post/article
- **relevance_score**: 0.0-1.0 how relevant to explaining the pump
- **sentiment**: positive/negative/neutral

Trigger types to identify:
- exchange_listing: New exchange listing
- partnership: Partnership announcement
- whale_activity: Large purchases
- influencer_mention: Celebrity/influencer tweet
- technical_breakout: Chart pattern
- news_article: News coverage
- unknown: Cannot determine

## Phase 3: Save to Database
Check if pump already exists - if so, add new findings to it:

```python
import sqlite3
conn = sqlite3.connect('{db_path}')

# Check if already exists in last hour
existing = conn.execute('SELECT id FROM pumps WHERE symbol = ? AND detected_at > datetime("now", "-1 hour")', (symbol,)).fetchone()
if existing:
    pump_id = existing[0]
    print(f"Adding findings to existing pump {{symbol}} (id={{pump_id}})")
else:
    # Save new pump
    cursor = conn.execute('''
        INSERT INTO pumps (symbol, price_change_pct, time_window_minutes, price_at_detection, volume_change_pct, market_cap, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (symbol, price_change_pct, time_window_minutes, price_at_detection, volume_change_pct, market_cap, source))
    pump_id = cursor.lastrowid
    print(f"Created new pump {{symbol}} (id={{pump_id}})")

# Save findings (must have actual content, not just "search performed")
for finding in findings:
    if finding.get('content') and len(finding['content']) > 50:
        # Check if this exact finding already exists
        exists = conn.execute('SELECT 1 FROM findings WHERE pump_id = ? AND content = ?', (pump_id, finding['content'])).fetchone()
        if not exists:
            conn.execute('''
                INSERT INTO findings (pump_id, source_type, source_url, content, relevance_score, sentiment)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (pump_id, finding['source_type'], finding.get('source_url'), finding['content'], finding.get('relevance_score', 0.5), finding.get('sentiment', 'neutral')))

# Save or update trigger (keep the one with higher confidence)
existing_trigger = conn.execute('SELECT confidence FROM news_triggers WHERE pump_id = ?', (pump_id,)).fetchone()
if not existing_trigger or existing_trigger[0] < confidence:
    conn.execute('DELETE FROM news_triggers WHERE pump_id = ?', (pump_id,))
    conn.execute('''
        INSERT INTO news_triggers (pump_id, trigger_type, description, confidence)
        VALUES (?, ?, ?, ?)
    ''', (pump_id, trigger_type, description, confidence))

conn.commit()
conn.close()
```

## Phase 4: Send Telegram Alert
Use the Telegram MCP `send_message` tool to send to chat ID from TELEGRAM_CHAT_ID environment variable.

Message format:
```
🚀 PUMP DETECTED: ${{symbol}}

📈 Price: +{{price_change_pct}}% (1h)
💰 Current: ${{price}}

🔍 Trigger: {{trigger_type}}
{{description}}

Key Findings:
- {{actual_tweet_or_news_text_1}}
- {{actual_tweet_or_news_text_2}}

#crypto #{{symbol}}
```

## Execution Rules

1. If no pumps detected, output "No pumps detected" and exit
2. For each pump, you MUST actually call the Twitter and Reddit MCPs - don't just say you searched
3. Findings must contain ACTUAL content from sources, not placeholders
4. Save each pump to database with real findings
5. Send Telegram message for each pump

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
