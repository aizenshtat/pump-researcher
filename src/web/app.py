"""
Flask web interface for viewing pump research results.
"""

import os
import re
from datetime import datetime

from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://pump:pump@postgres:5432/pump_researcher")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
from .models import db, Pump, Finding, NewsTrigger, AgentRun
db.init_app(app)

# Create tables on startup
with app.app_context():
    db.create_all()

# Celery task import
from src.worker.tasks import run_pump_agent

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pump Researcher</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0d1117;
            color: #c9d1d9;
        }
        h1, h2, h3 { color: #58a6ff; margin-top: 0; }
        .container { max-width: 1200px; margin: 0 auto; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #161b22;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #30363d;
        }
        .stat-value { font-size: 2em; font-weight: bold; color: #58a6ff; }
        .stat-label { color: #8b949e; font-size: 0.9em; }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .pump-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .symbol {
            font-size: 1.5em;
            font-weight: bold;
            color: #f0f6fc;
        }
        .change {
            font-size: 1.2em;
            padding: 5px 10px;
            border-radius: 4px;
        }
        .change.positive { background: #238636; color: #fff; }
        .trigger {
            background: #21262d;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
        }
        .trigger-type {
            text-transform: uppercase;
            font-size: 0.8em;
            color: #8b949e;
            margin-bottom: 5px;
        }
        .confidence {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            background: #30363d;
        }
        .confidence.high { background: #238636; }
        .confidence.medium { background: #9e6a03; }
        .confidence.low { background: #da3633; }
        .findings { margin-top: 15px; }
        .finding {
            padding: 10px;
            border-left: 3px solid #30363d;
            margin: 10px 0;
            background: #0d1117;
        }
        .finding-source {
            font-size: 0.8em;
            color: #8b949e;
            text-transform: uppercase;
        }
        .timestamp { color: #8b949e; font-size: 0.85em; }
        .empty { text-align: center; padding: 40px; color: #8b949e; }
        a { color: #58a6ff; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            background: #21262d;
            border-radius: 6px;
            cursor: pointer;
            border: 1px solid #30363d;
        }
        .tab.active { background: #58a6ff; color: #0d1117; border-color: #58a6ff; }
        .run-btn {
            padding: 10px 20px;
            background: #238636;
            color: #fff;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            margin-left: auto;
        }
        .run-btn:hover { background: #2ea043; }
        .run-btn:disabled { background: #30363d; cursor: not-allowed; }
        .view-logs-btn {
            padding: 4px 8px;
            background: #21262d;
            color: #58a6ff;
            border: 1px solid #30363d;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
        }
        .view-logs-btn:hover { background: #30363d; }
        .pump-nav {
            margin-left: 15px;
            font-size: 0.9em;
        }
        .nav-btn {
            background: #21262d;
            border: 1px solid #30363d;
            color: #58a6ff;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
        }
        .nav-btn:hover { background: #30363d; }
        .pump-index { margin: 0 8px; }
        .pump-meta {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .header-row {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        .status-msg {
            margin-left: 10px;
            font-size: 0.9em;
            color: #8b949e;
        }
        .log-container {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            max-height: 600px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.85em;
            display: none;
        }
        .log-container.visible { display: block; }
        .log-line { margin: 2px 0; white-space: pre-wrap; word-break: break-all; }
        .log-line.info { color: #58a6ff; }
        .log-line.success { color: #3fb950; }
        .log-line.error { color: #f85149; }
        .log-line.warn { color: #d29922; }
        .log-line.header { color: #f0883e; font-weight: bold; margin-top: 10px; }
        .collapsible {
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 4px;
            margin: 5px 0;
            overflow: hidden;
        }
        .collapsible-header {
            padding: 8px 12px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .collapsible-header:hover { background: #30363d; }
        .collapsible-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
            padding: 0 12px;
        }
        .collapsible.expanded .collapsible-content {
            max-height: 500px;
            overflow-y: auto;
            padding: 12px;
        }
        .collapsible-arrow { transition: transform 0.3s; }
        .collapsible.expanded .collapsible-arrow { transform: rotate(90deg); }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #30363d;
        }
        th { color: #8b949e; font-weight: normal; }

        /* Mobile responsive */
        @media (max-width: 768px) {
            body { padding: 10px; }
            .header-row {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            .run-btn { margin-left: 0; width: 100%; }
            .status-msg { margin-left: 0; }
            .stats { grid-template-columns: repeat(2, 1fr); gap: 10px; }
            .stat-card { padding: 15px; }
            .stat-value { font-size: 1.5em; }
            .tabs { flex-wrap: wrap; }
            .tab { flex: 1; text-align: center; min-width: 80px; }
            .card { padding: 15px; }
            .pump-header { flex-direction: column; align-items: flex-start; gap: 10px; }
            .symbol { font-size: 1.2em; }
            table { font-size: 0.85em; }
            th, td { padding: 8px 5px; }
            .log-container { font-size: 0.75em; max-height: 300px; }
            h1 { font-size: 1.5em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-row">
            <h1 style="margin: 0;">🔍 Pump Researcher</h1>
            <button class="run-btn" onclick="runAgent()" id="runBtn">▶ Run Agent</button>
            <span class="status-msg" id="statusMsg"></span>
        </div>

        <div class="log-container" id="logContainer"></div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_pumps }}</div>
                <div class="stat-label">Pumps Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_findings }}</div>
                <div class="stat-label">Findings</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_triggers }}</div>
                <div class="stat-label">Triggers Identified</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ stats.total_runs }}</div>
                <div class="stat-label">Agent Runs</div>
            </div>
        </div>

        <div class="tabs">
            <a href="/" class="tab {{ 'active' if tab == 'pumps' else '' }}">Pumps</a>
            <a href="/runs" class="tab {{ 'active' if tab == 'runs' else '' }}">Agent Runs</a>
        </div>

        {% if tab == 'pumps' %}
            {% if pump_groups %}
                {% for group in pump_groups %}
                <div class="card pump-group" data-symbol="{{ group.symbol }}">
                    <div class="pump-header">
                        <div>
                            <span class="symbol">{{ group.symbol }}</span>
                            {% if group.count > 1 %}
                            <span class="pump-nav">
                                <button class="nav-btn" onclick="prevPump('{{ group.symbol }}')">&lt;</button>
                                <span class="pump-index" id="idx-{{ group.symbol }}">1</span> / {{ group.count }}
                                <button class="nav-btn" onclick="nextPump('{{ group.symbol }}')">&gt;</button>
                            </span>
                            {% endif %}
                        </div>
                    </div>

                    {% for pump in group.pumps %}
                    <div class="pump-instance" id="pump-{{ group.symbol }}-{{ loop.index0 }}" {% if not loop.first %}style="display:none"{% endif %}>
                        <div class="pump-meta">
                            <span class="timestamp">{{ pump.detected_at }}</span>
                            <span class="change positive">+{{ "%.1f"|format(pump.price_change_pct) }}%</span>
                        </div>

                        {% if pump.trigger %}
                        <div class="trigger">
                            <div class="trigger-type">{{ pump.trigger.trigger_type | replace('_', ' ') }}</div>
                            <div>{{ pump.trigger.description }}</div>
                            <span class="confidence {{ 'high' if pump.trigger.confidence > 0.7 else 'medium' if pump.trigger.confidence > 0.4 else 'low' }}">
                                {{ "%.0f"|format(pump.trigger.confidence * 100) }}% confidence
                            </span>
                        </div>
                        {% endif %}

                        {% if pump.findings %}
                        <div class="findings">
                            <strong>Findings ({{ pump.findings|length }})</strong>
                            {% for finding in pump.findings[:5] %}
                            <div class="finding">
                                <div class="finding-source">{{ finding.source_type }}</div>
                                <div>{{ finding.content[:200] }}{% if finding.content|length > 200 %}...{% endif %}</div>
                                {% if finding.source_url %}
                                <a href="{{ finding.source_url }}" target="_blank">View source</a>
                                {% endif %}
                            </div>
                            {% endfor %}
                            {% if pump.findings|length > 5 %}
                            <div class="timestamp">... and {{ pump.findings|length - 5 }} more</div>
                            {% endif %}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
            {% else %}
                <div class="card empty">
                    <h3>No pumps detected yet</h3>
                    <p>Run the agent to start detecting pumps</p>
                </div>
            {% endif %}
        {% elif tab == 'runs' %}
            <div class="card">
                <table>
                    <thead>
                        <tr>
                            <th>Started</th>
                            <th>Status</th>
                            <th>Pumps</th>
                            <th>Findings</th>
                            <th>Duration</th>
                            <th>Logs</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for run in runs %}
                        <tr>
                            <td>{{ run.started_at }}</td>
                            <td>{{ run.status }}</td>
                            <td>{{ run.pumps_detected }}</td>
                            <td>{{ run.findings_count }}</td>
                            <td>{{ run.duration or '-' }}</td>
                            <td><button class="view-logs-btn" onclick="viewRunLogs({{ run.id }})">View</button></td>
                        </tr>
                        {% endfor %}
                        {% if not runs %}
                        <tr>
                            <td colspan="6" style="text-align: center; color: #8b949e;">No runs yet</td>
                        </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
            <div class="log-container" id="runLogContainer"></div>
        {% endif %}
    </div>
    <script>
        let logInterval = null;
        let lastLogIndex = 0;

        // Track current pump index for each symbol
        const pumpIndices = {};

        function getPumpCount(symbol) {
            const card = document.querySelector('[data-symbol="' + symbol + '"]');
            if (!card) return 0;
            return card.querySelectorAll('.pump-instance').length;
        }

        function showPump(symbol, index) {
            const count = getPumpCount(symbol);
            if (count === 0) return;

            // Wrap around
            if (index < 0) index = count - 1;
            if (index >= count) index = 0;

            pumpIndices[symbol] = index;

            // Hide all, show selected
            for (let i = 0; i < count; i++) {
                const el = document.getElementById('pump-' + symbol + '-' + i);
                if (el) el.style.display = i === index ? 'block' : 'none';
            }

            // Update counter
            const idxEl = document.getElementById('idx-' + symbol);
            if (idxEl) idxEl.textContent = index + 1;
        }

        function prevPump(symbol) {
            const current = pumpIndices[symbol] || 0;
            showPump(symbol, current - 1);
        }

        function nextPump(symbol) {
            const current = pumpIndices[symbol] || 0;
            showPump(symbol, current + 1);
        }

        async function runAgent() {
            const btn = document.getElementById('runBtn');
            const msg = document.getElementById('statusMsg');
            const logContainer = document.getElementById('logContainer');

            btn.disabled = true;
            btn.textContent = '⏳ Running...';
            msg.textContent = 'Agent started...';
            logContainer.innerHTML = '';
            logContainer.classList.add('visible');
            lastLogIndex = 0;
            inCollapsible = false;
            collapsibleContent = [];

            // Start polling for logs
            logInterval = setInterval(fetchLogs, 1000);

            try {
                const response = await fetch('/api/run', { method: 'POST' });
                const data = await response.json();

                // Stop polling
                clearInterval(logInterval);
                // Fetch final logs
                await fetchLogs();

                if (data.success) {
                    msg.textContent = '✓ Agent completed!';
                    btn.disabled = false;
                    btn.textContent = '▶ Run Agent';
                } else if (data.running) {
                    msg.textContent = '⚠ Agent is already running';
                    // Keep polling if already running
                    logInterval = setInterval(fetchLogs, 1000);
                } else {
                    msg.textContent = '✗ Error: ' + (data.error || 'Unknown error');
                    btn.disabled = false;
                    btn.textContent = '▶ Run Agent';
                }
            } catch (e) {
                clearInterval(logInterval);
                msg.textContent = '✗ Error: ' + e.message;
                btn.disabled = false;
                btn.textContent = '▶ Run Agent';
            }
        }

        let inCollapsible = false;
        let collapsibleContent = [];
        let collapsibleTitle = '';

        async function fetchLogs() {
            try {
                const response = await fetch('/api/logs?from=' + lastLogIndex);
                const data = await response.json();
                const logContainer = document.getElementById('logContainer');

                if (data.logs && data.logs.length > 0) {
                    data.logs.forEach(log => {
                        // Check for collapsible section markers
                        if (log.includes('=== PROMPT ===')) {
                            inCollapsible = true;
                            collapsibleTitle = '📋 Prompt (click to expand)';
                            collapsibleContent = [];
                            return;
                        } else if (log.includes('=== END PROMPT ===')) {
                            inCollapsible = false;
                            // Create collapsible element
                            const collapsible = createCollapsible(collapsibleTitle, collapsibleContent);
                            logContainer.appendChild(collapsible);
                            return;
                        }

                        if (inCollapsible) {
                            collapsibleContent.push(log);
                            return;
                        }

                        const line = document.createElement('div');
                        line.className = 'log-line';

                        // Color based on content
                        if (log.includes('error') || log.includes('Error') || log.includes('failed') || log.includes('✗')) {
                            line.classList.add('error');
                        } else if (log.includes('success') || log.includes('✓') || log.includes('completed')) {
                            line.classList.add('success');
                        } else if (log.includes('warning') || log.includes('⚠')) {
                            line.classList.add('warn');
                        } else if (log.includes('===') || log.includes('Starting') || log.includes('Generating')) {
                            line.classList.add('header');
                        } else if (log.includes('→') || log.includes('...')) {
                            line.classList.add('info');
                        }

                        line.textContent = log;
                        logContainer.appendChild(line);
                    });
                    logContainer.scrollTop = logContainer.scrollHeight;
                    lastLogIndex = data.index;
                }
            } catch (e) {
                console.error('Failed to fetch logs:', e);
            }
        }

        function createCollapsible(title, content) {
            const div = document.createElement('div');
            div.className = 'collapsible';

            const header = document.createElement('div');
            header.className = 'collapsible-header';
            header.onclick = function() { this.parentElement.classList.toggle('expanded'); };
            header.innerHTML = '<span>' + title + '</span><span class="collapsible-arrow">▶</span>';

            const contentDiv = document.createElement('div');
            contentDiv.className = 'collapsible-content';
            const pre = document.createElement('pre');
            pre.style.cssText = 'margin:0;white-space:pre-wrap;word-break:break-all;';
            pre.textContent = content.join('\\n');
            contentDiv.appendChild(pre);

            div.appendChild(header);
            div.appendChild(contentDiv);
            return div;
        }

        async function viewRunLogs(runId) {
            const logContainer = document.getElementById('runLogContainer');
            logContainer.innerHTML = 'Loading logs...';
            logContainer.classList.add('visible');

            try {
                const response = await fetch('/api/run/' + runId + '/logs');
                const data = await response.json();

                if (data.error) {
                    logContainer.innerHTML = 'Error: ' + data.error;
                    return;
                }

                logContainer.innerHTML = '';
                if (data.logs && data.logs.length > 0) {
                    data.logs.forEach(log => {
                        const line = document.createElement('div');
                        line.className = 'log-line';

                        // Try to parse and format JSON
                        let displayText = log;
                        if (log.trim().startsWith('{')) {
                            try {
                                const parsed = JSON.parse(log);
                                displayText = JSON.stringify(parsed, null, 2);
                                line.style.whiteSpace = 'pre';
                                line.style.fontSize = '0.75em';
                            } catch (e) {
                                // Not valid JSON, display as-is
                            }
                        }

                        if (log.includes('error') || log.includes('Error') || log.includes('failed') || log.includes('✗')) {
                            line.classList.add('error');
                        } else if (log.includes('success') || log.includes('✓') || log.includes('completed')) {
                            line.classList.add('success');
                        } else if (log.includes('warning') || log.includes('⚠')) {
                            line.classList.add('warn');
                        } else if (log.includes('===') || log.includes('Starting') || log.includes('Generating')) {
                            line.classList.add('header');
                        }

                        line.textContent = displayText;
                        logContainer.appendChild(line);
                    });
                } else {
                    logContainer.innerHTML = 'No logs available for this run';
                }
            } catch (e) {
                logContainer.innerHTML = 'Error loading logs: ' + e.message;
            }
        }
    </script>
</body>
</html>
"""

def get_stats():
    """Get dashboard statistics."""
    return {
        "total_pumps": db.session.query(Pump).count(),
        "total_findings": db.session.query(Finding).count(),
        "total_triggers": db.session.query(NewsTrigger).count(),
        "total_runs": db.session.query(AgentRun).count()
    }

@app.route("/")
def index():
    """Show pumps grouped by symbol with their findings and triggers."""
    grouped_pumps = {}

    pumps = Pump.query.order_by(Pump.detected_at.desc()).limit(100).all()

    for pump in pumps:
        pump_data = {
            "id": pump.id,
            "symbol": pump.symbol,
            "price_change_pct": pump.price_change_pct,
            "detected_at": pump.detected_at,
            "price_at_detection": pump.price_at_detection,
            "volume_change_pct": pump.volume_change_pct,
            "market_cap": pump.market_cap,
            "trigger": pump.trigger,
            "findings": pump.findings
        }

        # Group by symbol
        symbol = pump.symbol
        if symbol not in grouped_pumps:
            grouped_pumps[symbol] = []
        grouped_pumps[symbol].append(pump_data)

    # Convert to list of groups, sorted by most recent pump
    pump_groups = []
    for symbol, pumps_list in grouped_pumps.items():
        pump_groups.append({
            "symbol": symbol,
            "pumps": pumps_list,
            "count": len(pumps_list),
            "latest": pumps_list[0]  # Already sorted by detected_at DESC
        })

    # Sort by latest detection
    pump_groups.sort(key=lambda x: x["latest"]["detected_at"], reverse=True)

    return render_template_string(HTML_TEMPLATE,
                                  pump_groups=pump_groups,
                                  stats=get_stats(),
                                  tab="pumps")

@app.route("/runs")
def runs():
    """Show agent run history."""
    runs_list = []

    agent_runs = AgentRun.query.order_by(AgentRun.started_at.desc()).limit(100).all()

    for run in agent_runs:
        run_data = {
            "id": run.id,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "status": run.status,
            "pumps_detected": run.pumps_detected,
            "findings_count": run.findings_count,
            "duration": "completed" if run.completed_at and run.started_at else None
        }
        runs_list.append(run_data)

    return render_template_string(HTML_TEMPLATE,
                                  runs=runs_list,
                                  stats=get_stats(),
                                  tab="runs")

@app.route("/api/run", methods=["POST"])
def api_run_agent():
    """Trigger agent run via Celery."""
    # Check if there's already a running task
    running = AgentRun.query.filter_by(status="running").first()
    if running:
        return jsonify({"running": True, "message": "Agent is already running"})

    # Create agent run record
    agent_run = AgentRun(status="queued")
    db.session.add(agent_run)
    db.session.commit()
    run_id = agent_run.id

    # Queue the Celery task
    run_pump_agent.delay(run_id)

    return jsonify({"success": True, "message": "Agent queued", "run_id": run_id})

@app.route("/api/logs")
def get_logs():
    """Get logs from the most recent running or queued task."""
    from_index = int(request.args.get('from', 0))

    # Get the most recent run
    run = AgentRun.query.order_by(AgentRun.started_at.desc()).first()
    if not run or not run.logs:
        return jsonify({"logs": [], "index": 0})

    logs_list = run.logs.split('\n') if run.logs else []
    new_logs = logs_list[from_index:] if from_index < len(logs_list) else []
    return jsonify({"logs": new_logs, "index": len(logs_list)})

@app.route("/api/status")
def agent_status():
    """Check if agent is running."""
    running = AgentRun.query.filter(AgentRun.status.in_(["running", "queued"])).first() is not None
    return jsonify({"running": running})

@app.route("/api/run/<int:run_id>/logs")
def get_run_logs(run_id):
    """Get logs for a specific agent run."""
    run = AgentRun.query.get(run_id)

    if not run:
        return jsonify({"error": "Run not found"}), 404

    logs = run.logs or ""
    return jsonify({"logs": logs.split('\n') if logs else []})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
