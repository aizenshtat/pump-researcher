"""Celery tasks for running the pump research agent."""

import subprocess
import os
import re
from datetime import datetime
from pathlib import Path

from .celery_app import celery_app
from src.api.database import get_db_session
from src.api.models import AgentRun
from src.api.config import get_settings

settings = get_settings()


@celery_app.task(bind=True)
def run_pump_agent(self, run_id: int):
    """Run the pump research agent for a specific run."""

    with get_db_session() as db:
        run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
        if not run:
            return {"error": "Run not found"}

        run.status = "running"
        run.started_at = datetime.utcnow()
        db.commit()

        logs = []
        pumps_detected = 0
        findings_count = 0

        try:
            logs.append(f"Starting pump research agent (run #{run_id})")
            logs.append(f"Threshold: {settings.pump_threshold_pct}%")
            logs.append(f"Time window: {settings.pump_time_window_minutes} minutes")

            # Generate the orchestrator prompt
            from src.agents.orchestrator import generate_full_prompt
            prompt = generate_full_prompt(
                settings.pump_threshold_pct,
                settings.pump_time_window_minutes
            )
            logs.append(f"Prompt generated ({len(prompt)} bytes)")

            # Write prompt to temp file
            prompt_file = Path(f"/tmp/pump_prompt_{run_id}.txt")
            prompt_file.write_text(prompt)

            # Run Claude Code
            logs.append("Starting Claude Code...")

            # Only allow MCP tools - no file access, no bash
            cmd = [
                "claude",
                prompt,
                "--allowedTools", "mcp__*",
                "--output-format", "stream-json",
                "--verbose"
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd="/app"
            )

            # Stream output
            for line in iter(process.stdout.readline, ''):
                if line:
                    logs.append(line.rstrip())

                    # Extract stats from JSON output
                    if '"pumps_detected":' in line:
                        match = re.search(r'"pumps_detected":\s*(\d+)', line)
                        if match:
                            pumps_detected = int(match.group(1))
                    if '"findings_count":' in line:
                        match = re.search(r'"findings_count":\s*(\d+)', line)
                        if match:
                            findings_count = int(match.group(1))

            process.wait(timeout=600)

            if process.returncode == 0:
                run.status = "completed"
                logs.append("Agent completed successfully")
            else:
                run.status = "failed"
                logs.append(f"Agent exited with code {process.returncode}")

            # Cleanup
            prompt_file.unlink(missing_ok=True)

        except subprocess.TimeoutExpired:
            run.status = "timeout"
            logs.append("Agent timed out after 10 minutes")
            if process:
                process.kill()
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            logs.append(f"Error: {str(e)}")

        # Update run record
        run.completed_at = datetime.utcnow()
        run.pumps_detected = pumps_detected
        run.findings_count = findings_count
        run.logs = '\n'.join(logs)
        db.commit()

        return {
            "run_id": run_id,
            "status": run.status,
            "pumps_detected": pumps_detected,
            "findings_count": findings_count
        }


@celery_app.task
def run_pump_agent_scheduled():
    """Scheduled task to run pump detection."""
    with get_db_session() as db:
        run = AgentRun(status="queued")
        db.add(run)
        db.commit()
        run_id = run.id

    # Queue the actual task
    run_pump_agent.delay(run_id)
    return {"run_id": run_id, "status": "queued"}
