# Pump Researcher

Autonomous AI agent that detects crypto pumps and investigates their news triggers using Claude Code and MCP servers.

## Features

- **Pump Detection** - Monitors Binance and CoinMarketCap for significant price movements (default: ≥5% in 60 minutes)
- **Multi-Source Investigation** - Searches Reddit, Twitter/X, Discord, Telegram, and web for news triggers
- **AI Analysis** - Uses Claude to correlate pumps with news events and assess confidence
- **Real-time Dashboard** - Web UI with live agent logs, pump history, and findings
- **Automated Alerts** - Sends findings to Telegram channel
- **Scheduled Runs** - Hourly cron job via server deployment

**Live Demo:** https://pump-researcher.aizenshtat.eu

## Quick Start

```bash
cp .env.example .env
# Fill in API credentials
./scripts/run_agent.sh
```

Or with Docker:
```bash
docker compose up -d web              # Start web dashboard at :5000
docker compose run --rm pump-researcher  # Run agent once
```

## Configuration

### Required Secrets

For GitHub Actions deployment, add to Settings > Secrets > Actions:

| Secret | Description | Example |
|--------|-------------|---------|
| `SERVER_IP` | Server IP address | `91.99.4.56` |
| `SERVER_USER` | SSH username | `root` |
| `SERVER_DOMAIN` | Domain for SSL | `pump-researcher.aizenshtat.eu` |
| `SERVER_SSH_KEY` | SSH private key | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `CERTBOT_EMAIL` | Email for Let's Encrypt | `admin@example.com` |
| `ANTHROPIC_API_KEY` | Claude Code API key | |
| `TELEGRAM_CHAT_ID` | Telegram channel for alerts | |

### MCP Server Credentials

| Service | Get credentials at | Variables |
|---------|-------------------|-----------|
| Reddit | https://reddit.com/prefs/apps | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` |
| Telegram | https://my.telegram.org | `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_PHONE_NUMBER` |
| Twitter/X | https://developer.twitter.com | `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET` |
| Discord | Account credentials | `DISCORD_EMAIL`, `DISCORD_PASSWORD` |
| CoinMarketCap | https://coinmarketcap.com/api | `COINMARKETCAP_API_KEY`, `COINMARKETCAP_SUBSCRIPTION_LEVEL` |
| Binance | https://www.binance.com/en/my/settings/api-management | `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `BINANCE_TESTNET` |
| Grok/xAI | https://console.x.ai | `XAI_API_KEY` |

### Pump Detection Parameters

```bash
# Environment variables (or CLI flags)
PUMP_THRESHOLD_PCT=5.0        # --threshold
PUMP_TIME_WINDOW_MINUTES=60   # --window

# Examples
./scripts/run_agent.sh --threshold 10 --window 60    # 10% in 1 hour
./scripts/run_agent.sh --threshold 20 --window 1440  # 20% in 24 hours
```

## Deployment

### Local
```bash
./scripts/run_agent.sh              # Full run
./scripts/run_agent.sh --setup-only # Setup only
./scripts/run_agent.sh --skip-setup # Agent only
```

### Docker
```bash
docker compose run --rm pump-researcher  # One-off run
docker compose up -d web                 # Web interface at :5000
docker compose up -d scheduler           # Hourly scheduled runs
```

### Server (CI/CD)

After adding secrets, go to Actions > Deploy to Server > Run workflow.

This will:
1. Install Docker, nginx, certbot on first run
2. Get SSL certificate for your domain
3. Deploy and start containers
4. Setup hourly cron job

Web interface: https://pump-researcher.aizenshtat.eu

## Web Dashboard

The web interface provides:

- **Stats Overview** - Pumps detected, findings, triggers, agent runs
- **Run Agent Button** - Trigger agent manually with real-time log streaming
- **Pumps View** - All detected pumps with triggers and findings
- **Agent Runs** - History of all agent executions

Access locally at `http://localhost:5000` or via your deployed domain.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Detect Pumps    │ ──▶ │ Investigate News │ ──▶ │ Report Findings │
│ (Binance + CMC) │     │ (All Sources)    │     │ (SQLite + TG)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

**Data Sources:** Binance, CoinMarketCap, Reddit, Twitter, Discord, Telegram, Grok/xAI, Web Search

**Database:** SQLite at `data/research.db` with tables: `pumps`, `findings`, `news_triggers`, `notifications`, `agent_runs`

## Project Structure

```
├── .claude/settings.json       # MCP server configs
├── .env.example                # Environment template
├── .github/workflows/          # CI/CD (agent, deploy)
├── deploy/                     # nginx, server setup
├── scripts/
│   ├── run_agent.sh            # Main entry point
│   └── setup-mcp-servers.sh    # MCP installation
├── src/
│   ├── agents/                 # Detection, investigation, reporting
│   ├── db/                     # Schema and init
│   └── web/                    # Flask dashboard
├── Dockerfile
└── docker-compose.yml
```

## Troubleshooting

- **MCP server not loading**: Check env vars, run `which uvx` / `which npx`
- **Telegram auth**: Run `fast-mcp-telegram-setup`
- **Discord fails**: Run `uvx playwright install chromium`
- **SSH deployment fails**: Ensure `SERVER_SSH_KEY` is the private key (starts with `-----BEGIN`)

## License

MIT
