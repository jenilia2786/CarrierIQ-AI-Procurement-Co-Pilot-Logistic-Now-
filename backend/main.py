"""
CarrierIQ — AI-Powered Procurement Co-Pilot
FastAPI Main Application
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging

from app.database import connect_db, close_db, get_db
from app.config import settings
from app.api.auth import router as auth_router
from app.api.carriers import router as carriers_router
from app.api.chat import router as chat_router
from app.api.documents import rfq_router, award_router
from app.api.analytics import (
    scorecard_router, dashboard_router,
    benchmark_router, roi_router, onboard_router
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)


async def seed_database():
    """Seed MongoDB with mock carrier data on first run."""
    db = get_db()
    carrier_count = await db.carriers.count_documents({})
    if carrier_count == 0:
        from data.mock_data import CARRIERS_SEED, BENCHMARK_DATA
        await db.carriers.insert_many(CARRIERS_SEED)
        await db.benchmarks.insert_many(BENCHMARK_DATA)
        logger.info(f"[SEED] Seeded {len(CARRIERS_SEED)} carriers and {len(BENCHMARK_DATA)} benchmarks")

        # Mock ROI data
        roi_doc = {
            "user_id": "demo",
            "monthly_savings": [
                {"month": "Oct 2023", "savings": 42000, "rfqs": 3, "carriers_avoided": 1},
                {"month": "Nov 2023", "savings": 58000, "rfqs": 5, "carriers_avoided": 2},
                {"month": "Dec 2023", "savings": 71000, "rfqs": 4, "carriers_avoided": 1},
                {"month": "Jan 2024", "savings": 84500, "rfqs": 6, "carriers_avoided": 2},
                {"month": "Feb 2024", "savings": 93000, "rfqs": 7, "carriers_avoided": 3},
                {"month": "Mar 2024", "savings": 112000, "rfqs": 8, "carriers_avoided": 2},
            ],
            "total_savings": 460500,
            "total_rfqs_generated": 33,
            "underperforming_carriers_avoided": 11,
            "time_saved_hours": 247,
            "cost_per_kg_before": 22.5,
            "cost_per_kg_after": 17.8,
            "cost_reduction_pct": 20.9,
        }
        await db.roi_metrics.insert_one(roi_doc)
        logger.info("[SEED] Seeded ROI metrics")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    await seed_database()
    logger.info("CarrierIQ backend started successfully")
    yield
    await close_db()
    logger.info("CarrierIQ backend shutting down")


app = FastAPI(
    title="CarrierIQ API",
    description="AI-Powered Procurement Co-Pilot for Logistics",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth_router)
app.include_router(carriers_router)
app.include_router(chat_router)
app.include_router(rfq_router)
app.include_router(award_router)
app.include_router(scorecard_router)
app.include_router(dashboard_router)
app.include_router(benchmark_router)
app.include_router(roi_router)
app.include_router(onboard_router)

# Serve frontend static files
_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
_FRONTEND_DIR = os.path.abspath(_FRONTEND_DIR)
if os.path.exists(_FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=_FRONTEND_DIR), name="static")
    logger.info(f"[INFO] Frontend served from {_FRONTEND_DIR}")

@app.get("/app", response_class=FileResponse)
async def serve_frontend():
    return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))


@app.get("/")
async def root():
    return {
        "app": "CarrierIQ",
        "version": "1.0.0",
        "status": "operational",
        "ai_enabled": bool(settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here"),
        "message": "CarrierIQ — AI-Powered Procurement Co-Pilot is running",
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": __import__("datetime").datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
