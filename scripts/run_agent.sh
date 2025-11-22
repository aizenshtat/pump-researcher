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
THRESHOLD=""
WINDOW=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --setup-only) SETUP_ONLY=true ;;
        --skip-setup) SKIP_SETUP=true ;;
        --threshold) THRESHOLD="$2"; shift ;;
        --threshold=*) THRESHOLD="${1#*=}" ;;
        --window) WINDOW="$2"; shift ;;
        --window=*) WINDOW="${1#*=}" ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "  --setup-only        Only run setup, don't execute agent"
            echo "  --skip-setup        Skip setup, only run agent"
            echo "  --threshold PCT     Minimum price change % to detect (default: 5.0)"
            echo "  --window MINUTES    Time window in minutes (default: 60)"
            echo "  --help              Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 --threshold 10 --window 60    # 10% pumps in 1 hour"
            echo "  $0 --threshold 20 --window 1440  # 20% pumps in 24 hours"
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

# Build orchestrator arguments
ORCH_ARGS=""
if [ -n "$THRESHOLD" ]; then
    ORCH_ARGS="$ORCH_ARGS --threshold $THRESHOLD"
    echo "Using threshold: ${THRESHOLD}%"
fi
if [ -n "$WINDOW" ]; then
    ORCH_ARGS="$ORCH_ARGS --window $WINDOW"
    echo "Using time window: ${WINDOW} minutes"
fi

# Generate the prompt and save to temp file (avoids shell escaping issues)
PROMPT_FILE=$(mktemp)
echo "Generating prompt..."
python3 src/agents/orchestrator.py $ORCH_ARGS > "$PROMPT_FILE"
echo "Prompt generated ($(wc -c < "$PROMPT_FILE") bytes)"

# Execute with Claude Code in headless mode
# If running as root, switch to agent user (required for --dangerously-skip-permissions)
echo "Starting Claude Code..."
if [ "$(id -u)" = "0" ] && id agent &>/dev/null; then
    chown agent:agent "$PROMPT_FILE"
    # Also need to give agent access to app directory
    chown -R agent:agent /app/data 2>/dev/null || true
    su agent -c "cd /app && claude --print \"\$(cat $PROMPT_FILE)\" --allowedTools 'mcp__*' --dangerously-skip-permissions"
else
    claude --print "$(cat $PROMPT_FILE)" --allowedTools "mcp__*" --dangerously-skip-permissions
fi
CLAUDE_EXIT=$?
echo "Claude Code exited with code: $CLAUDE_EXIT"

rm -f "$PROMPT_FILE"

echo "=== Agent Run Completed ==="
