# Pump Researcher

Autonomous AI agent that detects crypto pumps and investigates their news triggers using Claude Code and multiple data sources.

## Features

- **Pump Detection**: Monitors Binance + CoinMarketCap for tokens with ≥5% gains in 1 hour
- **Multi-source Investigation**: Searches Reddit, Twitter, Discord, Telegram, web, and Grok/xAI
- **Automated Reporting**: Saves findings to SQLite and sends alerts to Telegram
- **Flexible Deployment**: Run locally, via Docker, or scheduled in GitHub Actions

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker (optional)

### Setup

1. **Clone and configure:**
   ```bash
   git clone <repo-url>
   cd pump-researcher
   cp .env.example .env
   ```

2. **Fill in API credentials** in `.env` (see [docs/MCP_SETUP.md](docs/MCP_SETUP.md) for details)

3. **Run the agent:**

   **Local (installs dependencies automatically):**
   ```bash
   ./scripts/run_agent.sh
   ```

   **Docker:**
   ```bash
   docker compose run --rm pump-researcher
   ```

## Deployment Options

### Local

```bash
# Full run (setup + agent)
./scripts/run_agent.sh

# Setup only
./scripts/run_agent.sh --setup-only

# Run only (skip setup)
./scripts/run_agent.sh --skip-setup
```

### Docker

```bash
# One-off run
docker compose run --rm pump-researcher

# Build image
docker compose build

# Scheduled (hourly via ofelia)
docker compose up -d scheduler

# Scheduled (hourly via cron)
docker compose --profile cron up -d cron-scheduler
```

### GitHub Actions (CI/CD)

1. Add secrets to repository (Settings > Secrets > Actions):
   - `ANTHROPIC_API_KEY`
   - `TELEGRAM_CHAT_ID`
   - All MCP credentials (see `.env.example`)

2. Agent runs automatically every hour, or trigger manually via Actions tab

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Detect Pumps    │ ──▶ │ Investigate News │ ──▶ │ Report Findings │
│ (Binance + CMC) │     │ (All Sources)    │     │ (SQLite + TG)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Data Sources

| Type | Sources |
|------|---------|
| Market Data | Binance, CoinMarketCap |
| Social | Reddit, Twitter/X, Discord, Telegram |
| AI Analysis | Grok/xAI, Web Search |

### Database Schema

Findings stored in `data/research.db`:
- `pumps` - Detected price movements
- `findings` - Individual news/social findings
- `news_triggers` - Identified causes with confidence scores
- `notifications` - Telegram message log
- `agent_runs` - Execution history

## Project Structure

```
.
├── .claude/settings.json      # MCP server configurations
├── .env.example               # Environment template
├── .github/workflows/         # CI/CD workflows
├── data/                      # SQLite database (gitignored)
├── docs/MCP_SETUP.md          # Detailed setup guide
├── scripts/
│   ├── run_agent.sh           # Main entry point
│   └── setup-mcp-servers.sh   # MCP installation
├── src/
│   ├── agents/                # Agent modules
│   └── db/                    # Database schema
├── Dockerfile
└── docker-compose.yml
```

## Documentation

- [MCP Setup Guide](docs/MCP_SETUP.md) - Detailed setup and configuration

## License

MIT
