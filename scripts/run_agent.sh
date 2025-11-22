#!/bin/bash
# Run the Pump Research Agent in headless mode
# Works both locally and in CI/CD

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Parse arguments
SETUP_ONLY=false
SKIP_SETUP=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --setup-only) SETUP_ONLY=true ;;
        --skip-setup) SKIP_SETUP=true ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "  --setup-only   Only run setup, don't execute agent"
            echo "  --skip-setup   Skip setup, only run agent"
            echo "  --help         Show this help"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# Load environment variables
if [ -f .env ]; then
    echo "Loading environment from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Setup phase (same as CI/CD)
if [ "$SKIP_SETUP" = false ]; then
    echo "=== Setup Phase ==="

    # Check for required tools
    if ! command -v node &> /dev/null; then
        echo "Error: Node.js is required. Install from https://nodejs.org"
        exit 1
    fi

    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        echo "Error: Python is required. Install from https://python.org"
        exit 1
    fi

    # Install Claude Code if not present
    if ! command -v claude &> /dev/null; then
        echo "Installing Claude Code..."
        npm install -g @anthropic-ai/claude-code
    fi

    # Run MCP servers setup (handles uv, MCP deps, cloning repos)
    if [ -f "$SCRIPT_DIR/setup-mcp-servers.sh" ]; then
        echo "Setting up MCP servers..."
        PUMP_RESEARCHER_SETUP=1 "$SCRIPT_DIR/setup-mcp-servers.sh"
    fi

    # Initialize database
    echo "Initializing database..."
    python src/db/init.py

    echo "=== Setup Complete ==="
fi

if [ "$SETUP_ONLY" = true ]; then
    echo "Setup complete. Use --skip-setup to run agent only."
    exit 0
fi

# Run agent phase
echo "=== Running Pump Research Agent ==="

# Generate the prompt
PROMPT=$(python src/agents/orchestrator.py)

# Execute with Claude Code in headless mode
# Same flags as CI/CD workflow
claude --print "$PROMPT" --allowedTools "mcp__*" --dangerously-skip-permissions

echo "=== Agent Run Completed ==="
