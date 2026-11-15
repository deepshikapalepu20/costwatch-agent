import logging
import os
import threading
import time
from contextlib import asynccontextmanager
 
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
 
from . import config, investigator, metrics
 
log = logging.getLogger("costwatch")
 
 
def _poll_loop():
    while True:
        try:
            metrics.refresh()
        except Exception:
            log.exception("Cost refresh failed")
        time.sleep(config.POLL_INTERVAL)
 
 
@asynccontextmanager
async def lifespan(app):
    threading.Thread(target=_poll_loop, daemon=True).start()
    yield
 
 
app = FastAPI(title="CostWatch Agent", lifespan=lifespan)
 
 
@app.get("/")
def home():
    return {
        "service": "CostWatch Agent",
        "endpoints": {
            "/alert": "POST - Alertmanager webhook",
            "/reports": "GET  - list incident reports",
            "/health": "GET  - health check",
            "/metrics": "GET  - Prometheus metrics",
        },
    }
 
 
@app.get("/health")
def health():
    return {"status": "healthy"}
 
 
@app.post("/alert")
async def alert(request: Request, background: BackgroundTasks):
    payload = await request.json()
    background.add_task(investigator.run, payload)
    return {"status": "accepted", "alerts": len(payload.get("alerts", []))}
 
 
@app.get("/reports")
def list_reports():
    if not os.path.isdir(config.REPORT_DIR):
        return []
    return sorted(os.listdir(config.REPORT_DIR), reverse=True)
 
 
@app.get("/reports/{name}")
def get_report(name: str):
    path = os.path.join(config.REPORT_DIR, os.path.basename(name))
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Report not found")
    with open(path, encoding="utf-8") as f:
        return {"name": name, "content": f.read()}
 
 
@app.get("/metrics")
def prometheus_metrics():
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

