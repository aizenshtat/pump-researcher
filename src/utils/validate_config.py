"""
Configuration validation for Pump Researcher.

Validates that required environment variables are set before running the agent.
"""

import os
import sys
from typing import Dict, List, Tuple


# Required credentials grouped by MCP server
REQUIRED_CREDENTIALS = {
    "anthropic": {
        "required": ["ANTHROPIC_API_KEY"],
        "description": "Claude API (required for agent execution)"
    },
    "binance": {
        "required": ["BINANCE_API_KEY", "BINANCE_API_SECRET"],
        "optional": ["BINANCE_TESTNET"],
        "description": "Binance exchange data"
    },
    "coinmarketcap": {
        "required": ["COINMARKETCAP_API_KEY"],
        "optional": ["COINMARKETCAP_SUBSCRIPTION_LEVEL"],
        "description": "CoinMarketCap market data"
    },
    "reddit": {
        "required": ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"],
        "description": "Reddit API for r/cryptocurrency searches"
    },
    "twitter": {
        "required": [],
        "optional": [
            "TWITTER_API_KEY", "TWITTER_API_SECRET",
            "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET",
            "TWITTER_USERNAME", "TWITTER_PASSWORD", "TWITTER_EMAIL"
        ],
        "description": "Twitter/X API for tweet searches"
    },
    "telegram": {
        "required": ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_PHONE_NUMBER"],
        "optional": ["TELEGRAM_CHAT_ID"],
        "description": "Telegram for channel searches and notifications"
    },
    "discord": {
        "required": ["DISCORD_EMAIL", "DISCORD_PASSWORD"],
        "description": "Discord for server searches"
    },
    "grok": {
        "required": ["XAI_API_KEY"],
        "description": "Grok/xAI for sentiment analysis"
    },
    "database": {
        "required": [],
        "optional": ["DATABASE_URL", "POSTGRES_PASSWORD"],
        "description": "PostgreSQL database connection"
    }
}

# Core services that must be configured
CORE_SERVICES = ["anthropic"]

# Data source services (at least one should be configured)
DATA_SOURCES = ["binance", "coinmarketcap"]

# Investigation sources (at least one should be configured)
INVESTIGATION_SOURCES = ["reddit", "twitter", "telegram", "discord", "grok"]


def check_credentials(service: str) -> Tuple[bool, List[str]]:
    """
    Check if credentials for a service are configured.

    Returns:
        Tuple of (all_required_present, missing_required)
    """
    config = REQUIRED_CREDENTIALS.get(service, {})
    required = config.get("required", [])

    missing = [var for var in required if not os.environ.get(var)]
    return len(missing) == 0, missing


def validate_all() -> Dict[str, dict]:
    """
    Validate all configured credentials.

    Returns:
        Dictionary with validation results for each service
    """
    results = {}

    for service, config in REQUIRED_CREDENTIALS.items():
        is_valid, missing = check_credentials(service)
        results[service] = {
            "valid": is_valid,
            "missing": missing,
            "description": config.get("description", "")
        }

    return results


def print_validation_report(results: Dict[str, dict]) -> bool:
    """
    Print a validation report and return True if core services are valid.
    """
    print("\n" + "=" * 60)
    print("PUMP RESEARCHER CONFIGURATION VALIDATION")
    print("=" * 60)

    all_valid = True
    data_source_valid = False
    investigation_source_valid = False

    # Check core services
    print("\n[CORE SERVICES]")
    for service in CORE_SERVICES:
        result = results.get(service, {})
        if result.get("valid"):
            print(f"  {service.upper()}: configured")
        else:
            print(f"  {service.upper()}: MISSING - {', '.join(result.get('missing', []))}")
            all_valid = False

    # Check data sources
    print("\n[DATA SOURCES] (at least one required)")
    for service in DATA_SOURCES:
        result = results.get(service, {})
        if result.get("valid"):
            print(f"  {service.upper()}: configured")
            data_source_valid = True
        else:
            print(f"  {service.upper()}: not configured")

    if not data_source_valid:
        print("  WARNING: No data sources configured!")
        all_valid = False

    # Check investigation sources
    print("\n[INVESTIGATION SOURCES] (at least one recommended)")
    for service in INVESTIGATION_SOURCES:
        result = results.get(service, {})
        if result.get("valid"):
            print(f"  {service.upper()}: configured")
            investigation_source_valid = True
        else:
            print(f"  {service.upper()}: not configured")

    if not investigation_source_valid:
        print("  WARNING: No investigation sources configured!")

    # Summary
    print("\n" + "-" * 60)
    if all_valid:
        print("STATUS: Ready to run")
    else:
        print("STATUS: Configuration incomplete")
        print("\nTo fix:")
        print("1. Copy .env.example to .env")
        print("2. Fill in the required API credentials")
        print("3. Run the agent again")
    print("=" * 60 + "\n")

    return all_valid


def validate_and_exit_on_failure():
    """
    Validate configuration and exit with error if core services missing.
    """
    results = validate_all()
    is_valid = print_validation_report(results)

    if not is_valid:
        sys.exit(1)


if __name__ == "__main__":
    # Run as standalone script
    from dotenv import load_dotenv
    load_dotenv()

    results = validate_all()
    is_valid = print_validation_report(results)
    sys.exit(0 if is_valid else 1)
