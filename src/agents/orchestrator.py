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

from db.init import init_db
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
Use the **postgres MCP** `query` and `execute` tools to save data. Do NOT use Python or Bash.

### Check if pump exists
```sql
SELECT id FROM pumps WHERE symbol = 'SYMBOL' AND detected_at > NOW() - INTERVAL '1 hour'
```

### If pump doesn't exist, create it
```sql
INSERT INTO pumps (symbol, price_change_pct, time_window_minutes, price_at_detection, volume_change_pct, market_cap, source)
VALUES ('SYMBOL', 10.5, 60, 1.23, 50.0, 1000000, 'binance')
RETURNING id
```

### Save findings (only if content length > 50)
```sql
INSERT INTO findings (pump_id, source_type, source_url, content, relevance_score, sentiment)
VALUES (PUMP_ID, 'twitter', 'https://...', 'Actual content here...', 0.8, 'positive')
ON CONFLICT DO NOTHING
```

### Save trigger (replace if higher confidence)
```sql
-- First check existing
SELECT confidence FROM news_triggers WHERE pump_id = PUMP_ID

-- Delete if new confidence is higher
DELETE FROM news_triggers WHERE pump_id = PUMP_ID

-- Insert new trigger
INSERT INTO news_triggers (pump_id, trigger_type, description, confidence)
VALUES (PUMP_ID, 'exchange_listing', 'Description of trigger', 0.85)
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
