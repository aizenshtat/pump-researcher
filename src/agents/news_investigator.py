"""
News Investigation Agent

Investigates detected pumps across multiple sources to find news triggers.
"""

import json
from datetime import datetime

def get_investigation_prompt(symbol: str, price_change_pct: float) -> str:
    """Generate investigation prompt for a specific pump."""
    return f"""
You are a crypto news investigation agent. Your task is to find the news trigger for a pump.

## Target
- **Symbol:** {symbol}
- **Price Change:** {price_change_pct:.1f}% in the last hour

## Investigation Sources (use in this order)

### 1. Reddit (via reddit MCP)
- Search r/cryptocurrency, r/CryptoMoonShots, r/{symbol.lower()} for recent posts
- Look for announcements, partnerships, or hype posts
- Get top posts from last 24 hours mentioning {symbol}

### 2. Twitter/X (via twitter MCP)
- Search for ${symbol} and #{symbol}
- Look for official announcements, influencer posts
- Check engagement metrics (likes, retweets)

### 3. Discord (via discord MCP)
- Check crypto trading servers for mentions
- Look for coordinated pump signals or news sharing

### 4. Telegram (via telegram MCP)
- Search crypto channels for {symbol} mentions
- Look for group discussions about the pump

### 5. Web Search (via WebSearch)
- Search for "{symbol} crypto news today"
- Search for "{symbol} announcement partnership"
- Look for press releases, blog posts, official announcements

### 6. Grok Analysis (via grok MCP)
- Ask Grok to analyze current sentiment and news around {symbol}
- Request live web search results about the token

## Analysis Guidelines
- Prioritize official sources (project Twitter, blog, Discord announcements)
- Note the timing - news should precede or coincide with the pump
- Look for: listings, partnerships, product launches, whale activity, social campaigns
- Assess credibility and relevance of each finding

## Output Format
Return a JSON object:
```json
{{
  "symbol": "{symbol}",
  "findings": [
    {{
      "source_type": "twitter",
      "source_url": "https://twitter.com/...",
      "content": "Brief summary of finding",
      "relevance_score": 0.85,
      "sentiment": "positive",
      "metadata": {{"likes": 1500, "retweets": 300}}
    }}
  ],
  "likely_trigger": {{
    "trigger_type": "partnership",
    "description": "Announced partnership with major exchange",
    "confidence": 0.8,
    "supporting_evidence": ["Summary of key evidence"]
  }},
  "summary": "One paragraph analysis of why this token pumped"
}}
```

Execute the investigation now and return ONLY the JSON output.
"""

TRIGGER_TYPES = [
    "announcement",      # Official project announcement
    "partnership",       # New partnership/collaboration
    "listing",          # Exchange listing
    "product_launch",   # New product or feature
    "social_hype",      # Influencer/viral social media
    "whale_activity",   # Large wallet movements
    "airdrop",          # Airdrop or rewards announcement
    "regulation",       # Regulatory news
    "market_trend",     # Following broader market
    "unknown"           # Could not determine
]

def parse_investigation_results(json_str: str) -> dict:
    """Parse investigation results from Claude Code output."""
    try:
        # Extract JSON from potential markdown code blocks
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        result = json.loads(json_str.strip())

        # Add timestamp
        result["investigated_at"] = datetime.utcnow().isoformat()

        return result
    except (json.JSONDecodeError, IndexError) as e:
        print(f"Error parsing investigation results: {e}")
        return {
            "symbol": "",
            "findings": [],
            "likely_trigger": {
                "trigger_type": "unknown",
                "description": f"Investigation failed: {e}",
                "confidence": 0.0
            },
            "summary": "Investigation could not be completed"
        }
