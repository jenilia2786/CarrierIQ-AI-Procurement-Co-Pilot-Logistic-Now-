from fastapi import APIRouter, HTTPException
from datetime import datetime
from bson import ObjectId

from app.database import get_db
from app.models.schemas import ScorecardUpdate, NewCarrierOnboard

router = APIRouter(tags=["Analytics"])

# ─── Scorecard ────────────────────────────────────────────────
scorecard_router = APIRouter(prefix="/scorecard")

@scorecard_router.post("/update")
async def update_scorecard(update: ScorecardUpdate):
    """Update carrier score after shipment completion."""
    db = get_db()

    # Calculate performance for this shipment
    from datetime import date
    try:
        actual = datetime.strptime(update.actual_delivery_date, "%Y-%m-%d").date()
        promised = datetime.strptime(update.promised_delivery_date, "%Y-%m-%d").date()
        delay_days = (actual - promised).days
        on_time = delay_days <= 0
    except:
        delay_days = 0
        on_time = True

    condition_score = {"good": 100, "partial": 70, "damaged": 20}.get(update.condition, 70)

    # Weighted shipment score
    shipment_score = (
        (100 if on_time else max(0, 100 - delay_days * 15)) * 0.40 +
        condition_score * 0.35 +
        update.billing_accuracy * 0.25
    )

    # Update carrier score in DB
    carrier = await db.carriers.find_one({"carrier_id": update.carrier_id})
    if carrier:
        old_score = carrier.get("computed_score", carrier.get("on_time_rate", 90))
        new_score = (old_score * 0.8 + shipment_score * 0.2)  # Exponential moving average
        await db.carriers.update_one(
            {"carrier_id": update.carrier_id},
            {
                "$set": {"computed_score": round(new_score, 1)},
                "$push": {"score_history": {"score": round(shipment_score, 1), "date": datetime.utcnow().isoformat()}},
            }
        )
    else:
        old_score = 90
        new_score = shipment_score

    # Record shipment
    shipment_doc = {
        "shipment_id": update.shipment_id,
        "carrier_id": update.carrier_id,
        "on_time": on_time,
        "delay_days": delay_days,
        "condition": update.condition,
        "billing_accuracy": update.billing_accuracy,
        "shipment_score": round(shipment_score, 1),
        "user_id": update.user_id,
        "recorded_at": datetime.utcnow(),
    }
    await db.shipments.insert_one(shipment_doc)

    return {
        "shipment_id": update.shipment_id,
        "carrier_id": update.carrier_id,
        "old_score": round(old_score, 1),
        "new_score": round(new_score, 1),
        "shipment_score": round(shipment_score, 1),
        "score_change": round(new_score - old_score, 1),
        "breakdown": {
            "on_time_component": (100 if on_time else max(0, 100 - delay_days * 15)),
            "condition_component": condition_score,
            "billing_component": update.billing_accuracy,
        },
    }


# ─── Dashboard Stats ──────────────────────────────────────────
dashboard_router = APIRouter(prefix="/dashboard")

@dashboard_router.get("/stats")
async def get_dashboard_stats(user_id: str = "demo"):
    """Aggregate dashboard metrics."""
    db = get_db()
    carrier_count = await db.carriers.count_documents({})
    bid_count = await db.bids.count_documents({"user_id": user_id})
    rfq_count = await db.rfqs.count_documents({"user_id": user_id})
    shipment_count = await db.shipments.count_documents({"user_id": user_id})
    chat_count = await db.chat_history.count_documents({"user_id": user_id})

    # ROI mock calculation
    avg_savings_per_shipment = 2800  # INR
    cost_saved = shipment_count * avg_savings_per_shipment + bid_count * 1500

    # Recent activity
    recent_bids = await db.bids.find({"user_id": user_id}).sort("created_at", -1).to_list(5)
    recent_activity = []
    for b in recent_bids:
        top = b.get("top_recommendation", {})
        recent_activity.append({
            "type": "bid_evaluation",
            "message": f"Bid evaluation — {top.get('carrier_name','') if top else 'Multiple'} selected",
            "time": b.get("created_at", datetime.utcnow()).isoformat() if hasattr(b.get("created_at", ""), "isoformat") else "recently",
        })

    # Carrier health summary
    top_carriers = await db.carriers.find({}).sort("on_time_rate", -1).to_list(5)
    carrier_health = [
        {"name": c["name"], "score": c.get("computed_score", c["on_time_rate"]), "status": "healthy" if c["on_time_rate"] >= 94 else ("watch" if c["on_time_rate"] >= 88 else "risk")}
        for c in top_carriers
    ]

    return {
        "total_carriers": carrier_count,
        "active_lanes": 7,
        "cost_saved_month": cost_saved if cost_saved > 0 else 84500,
        "pending_rfqs": max(0, rfq_count - (rfq_count // 2)),
        "total_bids_evaluated": bid_count,
        "total_shipments": shipment_count if shipment_count > 0 else 142,
        "chat_queries": chat_count,
        "recent_activity": recent_activity if recent_activity else [
            {"type": "bid_evaluation", "message": "BlueDart selected for Mumbai → Delhi lane", "time": "2 hours ago"},
            {"type": "rfq_generated", "message": "RFQ generated for Bangalore → Chennai", "time": "4 hours ago"},
            {"type": "fraud_alert", "message": "Fraud flag raised on DTDC Chen→Coim lane", "time": "Yesterday"},
        ],
        "carrier_health": carrier_health,
    }


# ─── Benchmark ────────────────────────────────────────────────
benchmark_router = APIRouter(prefix="/benchmark")

@benchmark_router.get("/lanes")
async def get_benchmark():
    db = get_db()
    benchmarks = await db.benchmarks.find({}).to_list(50)
    if not benchmarks:
        from data.mock_data import BENCHMARK_DATA
        benchmarks = BENCHMARK_DATA
    else:
        for b in benchmarks:
            b["_id"] = str(b["_id"])
    return {"benchmarks": benchmarks}


# ─── ROI ──────────────────────────────────────────────────────
roi_router = APIRouter(prefix="/roi")

@roi_router.get("/summary")
async def get_roi_summary(user_id: str = "demo"):
    db = get_db()
    roi_doc = await db.roi_metrics.find_one({"user_id": user_id})
    if not roi_doc:
        # Return realistic mock ROI data
        return {
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
    roi_doc["_id"] = str(roi_doc["_id"])
    return roi_doc


# ─── New Carrier Onboarding Scorer ────────────────────────────
onboard_router = APIRouter(prefix="/onboard")

@onboard_router.post("/score")
async def score_new_carrier(carrier: NewCarrierOnboard):
    """Score a new carrier for onboarding."""
    score = 0
    flags = []
    recommendations = []

    # Scoring heuristics
    if carrier.years_in_operation >= 10:
        score += 30
    elif carrier.years_in_operation >= 5:
        score += 20
        flags.append("Moderate experience — 5-10 years")
    else:
        score += 5
        flags.append("⚠️ New entrant — less than 5 years experience")

    if carrier.vehicle_count >= 100:
        score += 25
    elif carrier.vehicle_count >= 30:
        score += 15
    else:
        score += 5
        flags.append("⚠️ Small fleet size — capacity risk on high volume lanes")

    if len(carrier.coverage_cities) >= 20:
        score += 25
    elif len(carrier.coverage_cities) >= 10:
        score += 15
    else:
        score += 5
        flags.append("Limited coverage — suitable for specific lane contracts only")

    # GST validation (basic)
    if carrier.gst_number and len(carrier.gst_number) == 15:
        score += 10
    else:
        flags.append("⚠️ GST number format mismatch — verify before onboarding")

    # Certifications
    score += min(len(carrier.certifications) * 5, 10)

    trust_level = "HIGH" if score >= 75 else ("MEDIUM" if score >= 50 else "LOW")
    if trust_level == "HIGH":
        recommendations.append("✅ Approve for full contract — carrier meets all criteria")
    elif trust_level == "MEDIUM":
        recommendations.append("🔶 Approve for trial period — run 5 shipments before full contract")
        recommendations.append("Conduct background check on fleet, licenses, and previous clients")
    else:
        recommendations.append("❌ Reject or defer — insufficient credentials for contract award")
        recommendations.append("Request additional documentation before re-evaluation")

    return {
        "carrier_name": carrier.name,
        "trust_score": min(score, 100),
        "trust_level": trust_level,
        "flags": flags,
        "recommendations": recommendations,
        "breakdown": {
            "experience_score": min(30, score),
            "fleet_score": 25 if carrier.vehicle_count >= 100 else (15 if carrier.vehicle_count >= 30 else 5),
            "coverage_score": 25 if len(carrier.coverage_cities) >= 20 else (15 if len(carrier.coverage_cities) >= 10 else 5),
            "compliance_score": 10 if (carrier.gst_number and len(carrier.gst_number) == 15) else 0,
        }
    }
