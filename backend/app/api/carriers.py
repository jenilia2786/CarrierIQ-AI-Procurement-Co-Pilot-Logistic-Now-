import json
import csv
import io
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime
from bson import ObjectId

from app.database import get_db
from app.agents.master_agent import run_tool_directly
from data.mock_data import CARRIERS_SEED

router = APIRouter(prefix="/carriers", tags=["Carriers"])


@router.post("/upload-bids")
async def upload_bids(
    file: UploadFile = File(None),
    bids_json: str = Form(None),
    user_id: str = Form("demo"),
):
    """Upload carrier bids as CSV or JSON; agent normalizes and scores them."""
    raw_bids = []

    if file and file.filename:
        content = await file.read()
        if file.filename.endswith(".csv"):
            text = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            raw_bids = [dict(row) for row in reader]
        elif file.filename.endswith(".json"):
            raw_bids = json.loads(content.decode("utf-8"))
    elif bids_json:
        raw_bids = json.loads(bids_json)

    if not raw_bids:
        # Use mock bids to demonstrate
        raw_bids = [
            {"carrier_name": "BlueDart Express", "lane": "Mumbai → Delhi", "price": 18500, "transit_days": 2, "reliability_pct": 96.5},
            {"carrier_name": "Delhivery", "lane": "Mumbai → Delhi", "price": 16800, "transit_days": 2, "reliability_pct": 95.4},
            {"carrier_name": "Rivigo Technologies", "lane": "Mumbai → Delhi", "price": 22000, "transit_days": 2, "reliability_pct": 98.1},
            {"carrier_name": "Gati-KWE", "lane": "Mumbai → Delhi", "price": 19500, "transit_days": 3, "reliability_pct": 92.3},
            {"carrier_name": "XpressBees", "lane": "Mumbai → Delhi", "price": 15500, "transit_days": 2, "reliability_pct": 94.1},
        ]

    # Step 1: Normalize
    norm_result = run_tool_directly("BidNormalizerTool", {"raw_bids_list": raw_bids})
    print("DEBUG NORM:", norm_result)
    normalized = norm_result.get("normalized_bids", raw_bids)

    # Step 2: Score
    score_result = run_tool_directly("CarrierScorerTool", {"normalized_bids": normalized})
    print("DEBUG SCORE:", score_result)
    scored = score_result.get("scored_carriers", [])
    reasoning = score_result.get("reasoning", "")
    top = score_result.get("top_recommendation", scored[0] if scored else None)

    # Store bids in DB
    db = get_db()
    bid_doc = {
        "user_id": user_id,
        "raw_bids": raw_bids,
        "normalized_bids": normalized,
        "scored_carriers": scored,
        "top_recommendation": top,
        "reasoning": reasoning,
        "created_at": datetime.utcnow(),
    }
    result = await db.bids.insert_one(bid_doc)

    return {
        "bid_id": str(result.inserted_id),
        "normalized_bids": normalized,
        "scored_carriers": scored,
        "top_recommendation": top,
        "reasoning": reasoning,
    }


@router.get("/all")
async def get_all_carriers():
    """Return all carrier profiles."""
    db = get_db()
    carriers = await db.carriers.find({}).to_list(100)
    for c in carriers:
        c["_id"] = str(c["_id"])
    return {"carriers": carriers, "count": len(carriers)}


@router.get("/{carrier_id}")
async def get_carrier(carrier_id: str):
    """Return a single carrier's DNA profile."""
    db = get_db()
    carrier = await db.carriers.find_one({"carrier_id": carrier_id})
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    carrier["_id"] = str(carrier["_id"])

    # Enrich with risk data
    risk = run_tool_directly("RiskPredictorTool", {
        "carrier_name": carrier["name"],
        "lane": carrier.get("lanes", [""])[0],
    })
    fraud = run_tool_directly("FraudDetectorTool", {
        "carrier_name": carrier["name"],
        "billing_discrepancy_pct": carrier.get("fraud_score", 5) / 5,
        "pod_disputes": 0,
        "route_deviations": 0,
    })

    return {
        "carrier": carrier,
        "risk_profile": risk,
        "fraud_analysis": fraud,
    }


@router.get("/{carrier_id}/backup")
async def get_backup_carrier(carrier_id: str, lane: str = ""):
    """What-if backup recommender for a given carrier."""
    db = get_db()
    carrier = await db.carriers.find_one({"carrier_id": carrier_id})
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")

    # Get all carriers sorted by on_time_rate, exclude current
    all_carriers = await db.carriers.find({"carrier_id": {"$ne": carrier_id}}).sort("on_time_rate", -1).to_list(5)
    for c in all_carriers:
        c["_id"] = str(c["_id"])

    return {
        "primary_carrier": carrier["name"],
        "lane": lane or carrier.get("lanes", [""])[0],
        "backup_recommendations": all_carriers[:3],
        "reasoning": f"Based on reliability scores and lane coverage, {all_carriers[0]['name'] if all_carriers else 'N/A'} is the best backup carrier.",
    }
