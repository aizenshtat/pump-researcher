#!/bin/bash
set -e

echo "Setting up MCP servers..."

# Create .mcp-servers directory
MCP_DIR=".mcp-servers"
mkdir -p "$MCP_DIR"

# Install system dependencies
echo "Installing system dependencies..."

# Check for uv (Python package manager)
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Check for Node.js/npm
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required. Please install it first."
    exit 1
fi

# Install Python-based MCP servers
echo "Installing Python-based MCP servers..."

# Reddit MCP (via uvx)
echo "  - reddit-mcp (will be installed on first run via uvx)"

# Telegram MCP
echo "  - fast-mcp-telegram"
pip install fast-mcp-telegram || uv pip install fast-mcp-telegram

# Discord MCP (will be installed via uvx from git on first run)
echo "  - discord-mcp (will be installed on first run via uvx)"

# Grok MCP (requires cloning)
echo "  - Grok-MCP"
if [ ! -d "$MCP_DIR/Grok-MCP" ]; then
    git clone https://github.com/merterbak/Grok-MCP.git "$MCP_DIR/Grok-MCP"
    cd "$MCP_DIR/Grok-MCP"
    uv venv
    uv pip install -e .
    cd - > /dev/null
else
    echo "    Grok-MCP already exists, skipping clone"
fi

# Install Node.js-based MCP servers
echo "Installing Node.js-based MCP servers..."

# Twitter MCP (requires cloning and building)
echo "  - twitter-mcp-server"
if [ ! -d "$MCP_DIR/twitter-mcp-server" ]; then
    git clone https://github.com/taazkareem/twitter-mcp-server.git "$MCP_DIR/twitter-mcp-server"
    cd "$MCP_DIR/twitter-mcp-server"
    npm install
    npm run build
    cd - > /dev/null
else
    echo "    twitter-mcp-server already exists, skipping clone"
fi

# CoinMarketCap MCP (via npx, no pre-install needed)
echo "  - @shinzolabs/coinmarketcap-mcp (will be installed on first run via npx)"

# Binance MCP (via npx, no pre-install needed)
echo "  - binance-mcp-server (will be installed on first run via npx)"

# Install Playwright for Discord MCP
echo "Installing Playwright browsers for Discord MCP..."
uvx playwright install chromium || true

echo ""
echo "MCP server setup complete!"

# Only show next steps if running standalone (not from run_agent.sh)
if [ -z "$PUMP_RESEARCHER_SETUP" ]; then
    echo ""
    echo "Next steps:"
    echo "1. Copy .env.example to .env and fill in your API credentials"
    echo "2. For Telegram: run 'fast-mcp-telegram-setup' to authenticate"
    echo "3. Run ./run_agent.sh to start the research agent"
fi
