"""
Pump Detection Agent

Monitors Binance and CoinMarketCap for price movements.
This module provides prompts for Claude Code to execute via MCP servers.
"""

import json
import os
from datetime import datetime
from typing import Optional

# Pump detection configuration (can be overridden via environment variables)
PUMP_THRESHOLD_PCT = float(os.environ.get("PUMP_THRESHOLD_PCT", "5.0"))
TIME_WINDOW_MINUTES = int(os.environ.get("PUMP_TIME_WINDOW_MINUTES", "60"))

def get_detection_prompt(threshold_pct: float = None, time_window_minutes: int = None) -> str:
    """
    Get the pump detection prompt for Claude Code.

    Args:
        threshold_pct: Minimum price change percentage to detect (default: from env or 5.0)
        time_window_minutes: Time window for detection (default: from env or 60)
    """
    threshold = threshold_pct if threshold_pct is not None else PUMP_THRESHOLD_PCT
    window = time_window_minutes if time_window_minutes is not None else TIME_WINDOW_MINUTES

    # Convert minutes to human-readable format
    if window >= 1440:
        time_desc = f"{window // 1440} day{'s' if window >= 2880 else ''}"
    elif window >= 60:
        time_desc = f"{window // 60} hour{'s' if window >= 120 else ''}"
    else:
        time_desc = f"{window} minute{'s' if window != 1 else ''}"

    return f"""
You are a crypto pump detection agent. Your task is to identify tokens that have pumped significantly.

## Detection Criteria
- Price increase >= {threshold}% in the last {time_desc}
- Use BOTH Binance and CoinMarketCap data for comprehensive coverage

## Instructions

### Step 1: Get Binance Data
Use the Binance MCP server to:
1. Get list of all trading pairs (focus on USDT pairs)
2. Get price changes for the last {time_desc}
3. Filter for tokens with >= {threshold}% increase

### Step 2: Get CoinMarketCap Data
Use the CoinMarketCap MCP server to:
1. Get top gainers in the last {time_desc}
2. Get market cap and volume data for context

### Step 3: Combine and Deduplicate
- Merge results from both sources
- For tokens found in both, note as "both" source
- Include: symbol, price_change_pct, volume_change_pct, market_cap, current_price

### Output Format
Return a JSON array of detected pumps:
```json
[
  {{
    "symbol": "BTC",
    "price_change_pct": 7.5,
    "volume_change_pct": 150.2,
    "market_cap": 1200000000000,
    "price_at_detection": 65000.50,
    "source": "both",
    "time_window_minutes": {window}
  }}
]
```

If no pumps detected, return an empty array: []

Execute now and return ONLY the JSON output.
"""

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
