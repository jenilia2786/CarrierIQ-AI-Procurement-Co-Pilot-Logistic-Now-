import json
from fastapi import APIRouter, HTTPException
from datetime import datetime
from io import BytesIO
from bson import ObjectId

from app.database import get_db
from app.models.schemas import RFQRequest, AwardRequest
from app.agents.master_agent import run_tool_directly

router = APIRouter(tags=["Documents"])


# ─── RFQ ──────────────────────────────────────────────────────
rfq_router = APIRouter(prefix="/rfq")

@rfq_router.post("/generate")
async def generate_rfq(req: RFQRequest):
    """Generate a complete RFQ document using LLM."""
    result = run_tool_directly("RFQGeneratorTool", {
        "origin": req.origin,
        "destination": req.destination,
        "cargo_type": req.cargo_type,
        "weight_kg": req.weight_kg,
        "volume_cbm": req.volume_cbm,
        "pickup_date": req.pickup_date,
        "delivery_deadline": req.delivery_deadline,
        "special_requirements": req.special_requirements,
    })

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))

    rfq_text = result["rfq_text"]
    db = get_db()
    doc = {
        "user_id": req.user_id,
        "origin": req.origin,
        "destination": req.destination,
        "rfq_text": rfq_text,
        "created_at": datetime.utcnow(),
        "status": "draft",
    }
    res = await db.rfqs.insert_one(doc)
    return {"rfq_id": str(res.inserted_id), "rfq_text": rfq_text}


@rfq_router.get("/list/{user_id}")
async def list_rfqs(user_id: str):
    db = get_db()
    rfqs = await db.rfqs.find({"user_id": user_id}).sort("created_at", -1).to_list(20)
    for r in rfqs:
        r["_id"] = str(r["_id"])
        r["created_at"] = r["created_at"].isoformat() if hasattr(r.get("created_at"), "isoformat") else str(r.get("created_at",""))
    return {"rfqs": rfqs}


# ─── Award Letter ─────────────────────────────────────────────
award_router = APIRouter(prefix="/award")

@award_router.post("/generate")
async def generate_award(req: AwardRequest):
    """Generate a formal carrier award letter."""
    result = run_tool_directly("AwardLetterTool", {
        "carrier_name": req.carrier_name,
        "lane": req.lane,
        "rate": req.rate,
        "sla_terms": req.sla_terms,
        "effective_date": req.effective_date,
    })

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))

    letter_text = result["award_letter"]
    db = get_db()
    doc = {
        "user_id": req.user_id,
        "carrier_name": req.carrier_name,
        "lane": req.lane,
        "rate": req.rate,
        "letter_text": letter_text,
        "created_at": datetime.utcnow(),
        "status": "issued",
    }
    res = await db.awards.insert_one(doc)
    return {"award_id": str(res.inserted_id), "letter_text": letter_text}


@award_router.get("/list/{user_id}")
async def list_awards(user_id: str):
    db = get_db()
    awards = await db.awards.find({"user_id": user_id}).sort("created_at", -1).to_list(20)
    for a in awards:
        a["_id"] = str(a["_id"])
        a["created_at"] = a["created_at"].isoformat() if hasattr(a.get("created_at"), "isoformat") else str(a.get("created_at",""))
    return {"awards": awards}
