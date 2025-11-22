"""
Pump Detection Agent

Monitors Binance and CoinMarketCap for price movements exceeding 5% in 1 hour.
This module provides prompts for Claude Code to execute via MCP servers.
"""

import json
from datetime import datetime
from typing import Optional

# Pump detection configuration
PUMP_THRESHOLD_PCT = 5.0
TIME_WINDOW_MINUTES = 60

DETECT_PUMPS_PROMPT = """
You are a crypto pump detection agent. Your task is to identify tokens that have pumped significantly.

## Detection Criteria
- Price increase >= 5% in the last 1 hour
- Use BOTH Binance and CoinMarketCap data for comprehensive coverage

## Instructions

### Step 1: Get Binance Data
Use the Binance MCP server to:
1. Get list of all trading pairs (focus on USDT pairs)
2. Get 1-hour price changes for each
3. Filter for tokens with >= 5% increase

### Step 2: Get CoinMarketCap Data
Use the CoinMarketCap MCP server to:
1. Get top gainers in the last 1 hour
2. Get market cap and volume data for context

### Step 3: Combine and Deduplicate
- Merge results from both sources
- For tokens found in both, note as "both" source
- Include: symbol, price_change_pct, volume_change_pct, market_cap, current_price

### Output Format
Return a JSON array of detected pumps:
```json
[
  {
    "symbol": "BTC",
    "price_change_pct": 7.5,
    "volume_change_pct": 150.2,
    "market_cap": 1200000000000,
    "price_at_detection": 65000.50,
    "source": "both",
    "time_window_minutes": 60
  }
]
```

If no pumps detected, return an empty array: []

Execute now and return ONLY the JSON output.
"""

def get_detection_prompt() -> str:
    """Get the pump detection prompt for Claude Code."""
    return DETECT_PUMPS_PROMPT

def parse_pump_results(json_str: str) -> list[dict]:
    """Parse pump detection results from Claude Code output."""
    try:
        # Extract JSON from potential markdown code blocks
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        pumps = json.loads(json_str.strip())

        # Validate and enrich each pump
        for pump in pumps:
            pump["detected_at"] = datetime.utcnow().isoformat()
            pump.setdefault("time_window_minutes", TIME_WINDOW_MINUTES)

        return pumps
    except (json.JSONDecodeError, IndexError) as e:
        print(f"Error parsing pump results: {e}")
        return []
