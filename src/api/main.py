"""FastAPI backend for Pump Researcher."""

from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import get_db, init_db
from .models import Pump, Finding, NewsTrigger, AgentRun
from .config import get_settings

app = FastAPI(
    title="Pump Researcher API",
    description="API for crypto pump detection and research",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = get_settings()


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    return {
        "total_pumps": db.query(func.count(Pump.id)).scalar(),
        "total_findings": db.query(func.count(Finding.id)).scalar(),
        "total_triggers": db.query(func.count(NewsTrigger.id)).scalar(),
        "total_runs": db.query(func.count(AgentRun.id)).scalar()
    }


@app.get("/api/pumps")
async def get_pumps(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent pumps with findings and triggers."""
    pumps = db.query(Pump).order_by(Pump.detected_at.desc()).limit(limit).all()

    result = []
    for pump in pumps:
        pump_data = {
            "id": pump.id,
            "symbol": pump.symbol,
            "price_change_pct": pump.price_change_pct,
            "detected_at": pump.detected_at.isoformat() if pump.detected_at else None,
            "price_at_detection": pump.price_at_detection,
            "volume_change_pct": pump.volume_change_pct,
            "market_cap": pump.market_cap,
            "trigger": None,
            "findings": []
        }

        if pump.trigger:
            pump_data["trigger"] = {
                "trigger_type": pump.trigger.trigger_type,
                "description": pump.trigger.description,
                "confidence": pump.trigger.confidence
            }

        for finding in pump.findings[:5]:  # Limit to 5 findings
            pump_data["findings"].append({
                "source_type": finding.source_type,
                "content": finding.content,
                "source_url": finding.source_url,
                "relevance_score": finding.relevance_score,
                "sentiment": finding.sentiment
            })

        result.append(pump_data)

    return result


@app.get("/api/runs")
async def get_runs(limit: int = 100, db: Session = Depends(get_db)):
    """Get agent run history."""
    runs = db.query(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit).all()

    return [{
        "id": run.id,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "pumps_detected": run.pumps_detected,
        "findings_count": run.findings_count,
        "status": run.status,
        "error_message": run.error_message
    } for run in runs]


@app.get("/api/runs/{run_id}/logs")
async def get_run_logs(run_id: int, db: Session = Depends(get_db)):
    """Get logs for a specific run."""
    run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    logs = run.logs.split('\n') if run.logs else []
    return {"logs": logs}


@app.post("/api/runs")
async def trigger_run(db: Session = Depends(get_db)):
    """Trigger a new agent run."""
    from .worker.tasks import run_pump_agent

    # Create run record
    run = AgentRun(status="queued")
    db.add(run)
    db.commit()
    db.refresh(run)

    # Queue the task
    run_pump_agent.delay(run.id)

    return {"run_id": run.id, "status": "queued"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
