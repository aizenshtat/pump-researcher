FROM node:20-slim

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Install Claude Code
RUN npm install -g @anthropic-ai/claude-code

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.sh

# Install Flask for web interface
RUN pip3 install flask --break-system-packages

# Setup MCP servers
RUN PUMP_RESEARCHER_SETUP=1 ./scripts/setup-mcp-servers.sh

# Initialize database directory
RUN mkdir -p data

# Create non-root user for Claude Code
RUN useradd -m -s /bin/bash agent && \
    chown -R agent:agent /app

# Default command (switch to agent user for Claude Code)
CMD ["./scripts/run_agent.sh", "--skip-setup"]
