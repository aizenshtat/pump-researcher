# MCP Server Setup Guide

This project uses multiple MCP (Model Context Protocol) servers to integrate with various platforms.

## Quick Start

### Local Development

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your API credentials** in `.env`

3. **Run the agent:**
   ```bash
   ./scripts/run_agent.sh
   ```
   This automatically installs dependencies, sets up MCP servers, and runs the agent.

### Docker

```bash
# One-off run
docker compose run --rm pump-researcher

# Scheduled (hourly)
docker compose up -d scheduler
```

### CI/CD Setup (GitHub Actions)

1. **Add secrets to GitHub repository:**
   - Go to Settings > Secrets and variables > Actions
   - Add all environment variables from `.env.example` as secrets
   - Required: `ANTHROPIC_API_KEY`, `TELEGRAM_CHAT_ID`, plus all MCP credentials

2. **Trigger the workflow:**
   - Runs automatically every hour
   - Or manually trigger via Actions > Pump Research Agent > Run workflow

The CI/CD workflow builds and runs the same Docker image used locally.

## MCP Servers

### Reddit
- **Source:** [GridfireAI/reddit-mcp](https://github.com/GridfireAI/reddit-mcp)
- **Credentials:** https://reddit.com/prefs/apps (create a "script" type app)
- **Variables:**
  - `REDDIT_CLIENT_ID`
  - `REDDIT_CLIENT_SECRET`

### Telegram
- **Source:** [leshchenko1979/tg_mcp](https://github.com/leshchenko1979/tg_mcp)
- **Credentials:** https://my.telegram.org (API development tools)
- **Setup:** After installing, run `fast-mcp-telegram-setup` to authenticate
- **Variables:**
  - `TELEGRAM_API_ID`
  - `TELEGRAM_API_HASH`
  - `TELEGRAM_PHONE_NUMBER`

### Twitter/X
- **Source:** [taazkareem/twitter-mcp-server](https://github.com/taazkareem/twitter-mcp-server)
- **Credentials:** Your Twitter account credentials
- **Variables:**
  - `TWITTER_USERNAME`
  - `TWITTER_PASSWORD`
  - `TWITTER_EMAIL`

### Discord
- **Source:** [elyxlz/discord-mcp](https://github.com/elyxlz/discord-mcp)
- **Credentials:** Your Discord account credentials
- **Note:** Uses browser automation via Playwright
- **Variables:**
  - `DISCORD_EMAIL`
  - `DISCORD_PASSWORD`

### CoinMarketCap
- **Source:** [shinzo-labs/coinmarketcap-mcp](https://github.com/shinzo-labs/coinmarketcap-mcp)
- **Credentials:** https://coinmarketcap.com/api (free tier available)
- **Variables:**
  - `COINMARKETCAP_API_KEY`
  - `COINMARKETCAP_SUBSCRIPTION_LEVEL` (Basic, Hobbyist, Startup, Standard, Professional, Enterprise)

### Binance
- **Source:** [ethancod1ng/binance-mcp-server](https://github.com/ethancod1ng/binance-mcp-server)
- **Credentials:** https://www.binance.com/en/my/settings/api-management
- **Variables:**
  - `BINANCE_API_KEY`
  - `BINANCE_API_SECRET`
  - `BINANCE_TESTNET` (set to `true` for testing with virtual funds)

### Grok (xAI)
- **Source:** [merterbak/Grok-MCP](https://github.com/merterbak/Grok-MCP)
- **Credentials:** https://console.x.ai
- **Variables:**
  - `XAI_API_KEY`

## Pump Research Agent

The project includes an autonomous research agent that runs hourly to detect crypto pumps and investigate their causes.

### How It Works

1. **Pump Detection** - Monitors Binance + CoinMarketCap for tokens with ≥5% gains in 1 hour
2. **News Investigation** - Searches Reddit, Twitter, Discord, Telegram, web, and Grok for news triggers
3. **Reporting** - Saves findings to SQLite database and sends alerts to Telegram

### Running the Agent

**Local:**
```bash
./run_agent.sh
```

**CI/CD:**
- Runs automatically every hour via GitHub Actions
- Manually trigger: Actions > Pump Research Agent > Run workflow

### Agent Workflow
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Detect Pumps    │ ──▶ │ Investigate News │ ──▶ │ Report Findings │
│ (Binance + CMC) │     │ (All Sources)    │     │ (SQLite + TG)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Database Schema

Findings are stored in `data/research.db`:
- `pumps` - Detected price movements
- `findings` - Individual news/social findings
- `news_triggers` - Identified causes with confidence scores
- `notifications` - Telegram message log
- `agent_runs` - Execution history

### Required Secrets for CI/CD

Add these to GitHub Secrets (Settings > Secrets > Actions):
- `ANTHROPIC_API_KEY` - For Claude Code
- `TELEGRAM_CHAT_ID` - Where to send alerts
- All MCP server credentials (see above)

## File Structure

```
.
├── .claude/
│   └── settings.local.json    # MCP server configurations
├── .env.example               # Template for environment variables
├── .env                       # Your actual credentials (gitignored)
├── .mcp-servers/              # Cloned MCP server repos
│   ├── twitter-mcp-server/
│   └── Grok-MCP/
├── .github/
│   └── workflows/
│       ├── setup-mcp.yml            # MCP setup workflow
│       └── pump-research-agent.yml  # Hourly agent workflow
├── data/
│   └── research.db            # SQLite database (gitignored)
├── src/
│   ├── db/
│   │   ├── schema.sql         # Database schema
│   │   └── init.py            # DB initialization
│   └── agents/
│       ├── pump_detector.py   # Pump detection prompts
│       ├── news_investigator.py # Investigation prompts
│       ├── reporter.py        # SQLite + Telegram reporting
│       └── orchestrator.py    # Main workflow coordinator
├── scripts/
│   └── setup-mcp-servers.sh   # Setup script
└── run_agent.sh               # Local run script
```

## Troubleshooting

### Server not loading
- Ensure all required environment variables are set
- Check Claude Code logs for errors
- Verify the server command exists (e.g., `which uvx`, `which npx`)

### Authentication issues
- **Telegram:** Re-run `fast-mcp-telegram-setup`
- **Discord:** Ensure Playwright browsers are installed: `uvx playwright install chromium`

### Missing dependencies
- **Python servers:** Ensure `uv` is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node servers:** Ensure Node.js 18+ is installed

## Security Notes

- Never commit `.env` to version control
- Use GitHub Secrets for CI/CD
- Consider using API keys with minimal required permissions
- For Binance, enable IP whitelist and use testnet for development
