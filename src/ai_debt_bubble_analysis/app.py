# src/ai_debt_bubble_analysis/app.py
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import load_config
from .service import AnalysisEngine

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    engine = AnalysisEngine(config)
    await engine.initialize()
    app.state.engine = engine
    initial_refresh = asyncio.create_task(engine.refresh(force=True))
    try:
        yield
    finally:
        if not initial_refresh.done():
            initial_refresh.cancel()
            await asyncio.gather(initial_refresh, return_exceptions=True)
        await engine.close()


app = FastAPI(
    title="AI Debt Bubble Analysis",
    version="0.1.0",
    description="Market wealth, leverage and shadow-obligation monitor.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "ai-debt-bubble-analysis"}


@app.get("/api/overview")
async def overview():
    engine: AnalysisEngine = app.state.engine
    snapshot = await engine.refresh()
    return snapshot.to_dict()


@app.post("/api/refresh")
async def refresh():
    engine: AnalysisEngine = app.state.engine
    snapshot = await engine.refresh(force=True)
    return snapshot.to_dict()


@app.get("/api/history")
async def history(limit: int = Query(default=120, ge=1, le=2000)):
    engine: AnalysisEngine = app.state.engine
    return await engine.history(limit)


@app.get("/api/company/{ticker}")
async def company(ticker: str):
    engine: AnalysisEngine = app.state.engine
    snapshot = await engine.refresh()
    target = ticker.upper()
    for item in snapshot.companies:
        if item.ticker == target:
            return item
    raise HTTPException(status_code=404, detail=f"Unknown monitored ticker: {target}")
