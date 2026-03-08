"""
CarrierIQ Master LangChain Agent — LangChain 1.x compatible
Uses tool calling via ChatOpenAI bind_tools with a manual execution loop.
All 8 tools: BidNormalizer, CarrierScorer, RiskPredictor, RAGQuery,
RFQGenerator, AwardLetter, FraudDetector, SeasonalPredictor
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

from app.config import settings
from app.rag.rag_engine import query_rag

logger = logging.getLogger(__name__)


# ─── Tool Implementations ─────────────────────────────────────────────────────

@tool
def BidNormalizerTool(raw_bids_list: Any) -> str:
    """
    Normalizes carrier bid data from various formats into a standardized structure.
    Arguments:
    - raw_bids_list: A list of dictionaries, each representing a carrier bid with fields like 'carrier', 'lane', 'price'.
    """
    try:
        if isinstance(raw_bids_list, str):
            bids = json.loads(raw_bids_list)
        else:
            bids = raw_bids_list
        normalized = []

        for b in bids:
            norm = {
                "carrier_name": b.get("carrier_name") or b.get("Carrier") or b.get("carrier") or "Unknown Carrier",
                "lane": b.get("lane") or b.get("Route") or b.get("route") or "Unknown Lane",
                "price": float(b.get("price") or b.get("Rate") or b.get("rate") or b.get("cost") or 0),
                "transit_days": int(b.get("transit_days") or b.get("Days") or b.get("transit") or 3),
                "reliability_pct": float(b.get("reliability_pct") or b.get("Reliability") or b.get("on_time") or 90),
                "weight_limit_kg": float(b.get("weight_limit_kg") or b.get("Weight Limit") or 5000),
                "vehicle_type": b.get("vehicle_type") or b.get("Vehicle") or "Truck",
                "gst_included": True,
            }
            normalized.append(norm)
        return json.dumps({"status": "success", "normalized_bids": normalized, "count": len(normalized)})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def CarrierScorerTool(normalized_bids: Any) -> str:
    """
    Scores carriers on Price, Reliability, Transit Time, and Risk.
    Arguments:
    - normalized_bids: A list of normalized bid dictionaries.
    """
    try:
        if isinstance(normalized_bids, str):
            bids = json.loads(normalized_bids)
        else:
            bids = normalized_bids

        prices = [b["price"] for b in bids if b.get("price", 0) > 0]
        min_price, max_price = (min(prices), max(prices)) if prices else (1, 1)
        transits = [b.get("transit_days", 3) for b in bids]
        min_transit, max_transit = (min(transits), max(transits)) if transits else (1, 1)

        scored = []
        for b in bids:
            price_rng = max_price - min_price if max_price != min_price else 1
            price_score = (1 - (b.get("price", 0) - min_price) / price_rng) * 100
            reliability_score = float(b.get("reliability_pct", 90))
            transit_rng = max_transit - min_transit if max_transit != min_transit else 1
            transit_score = (1 - (b.get("transit_days", 3) - min_transit) / transit_rng) * 100
            risk_score = max(0, min(100, 100 - b.get("reliability_pct", 90) * 0.5))
            total = price_score * 0.30 + reliability_score * 0.35 + transit_score * 0.20 + risk_score * 0.15

            scored.append({
                **b,
                "price_score": round(price_score, 1),
                "reliability_score": round(reliability_score, 1),
                "transit_score": round(transit_score, 1),
                "risk_score": round(risk_score, 1),
                "total_score": round(total, 1),
                "recommendation": "Recommended" if total >= 75 else ("Consider" if total >= 60 else "Avoid"),
            })

        scored.sort(key=lambda x: x["total_score"], reverse=True)
        top = scored[0] if scored else None
        reasoning = ""
        if top:
            reasoning = (
                f"**Top Recommendation: {top['carrier_name']}** (Score: {top['total_score']}/100)\n\n"
                f"**Why {top['carrier_name']} wins:**\n"
                f"• Price competitiveness: {top['price_score']}/100 — offers ₹{top.get('price',0):,.0f}\n"
                f"• Reliability: {top['reliability_score']}/100 — {top.get('reliability_pct',0)}% on-time rate\n"
                f"• Transit efficiency: {top['transit_score']}/100 — delivers in {top.get('transit_days',0)} days\n"
                f"• Risk profile: {top['risk_score']}/100\n\n"
                f"**Weight formula:** Price (30%) + Reliability (35%) + Transit (20%) + Risk (15%)"
            )

        return json.dumps({"status": "success", "scored_carriers": scored, "top_recommendation": top, "reasoning": reasoning})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def RiskPredictorTool(carrier_name: str, lane: str) -> str:
    """
    Predicts delay and risk probability for a carrier on a specific lane.
    """
    try:
        carrier = carrier_name
        lane = lane
        context = query_rag(f"{carrier} {lane} risk delay fraud", k=3)
        risk_keywords = {"theft": 20, "fake pod": 25, "overbilling": 15, "fraud": 20, "delay": 10, "monsoon": 8, "festive": 8}
        base_risk = 10
        flags = []
        ctx_text = " ".join(context).lower()
        for kw, pts in risk_keywords.items():
            if kw in ctx_text:
                base_risk += pts
                flags.append(kw.title())
        risk_level = "LOW" if base_risk < 20 else ("MEDIUM" if base_risk < 40 else "HIGH")
        return json.dumps({
            "status": "success", "carrier": carrier, "lane": lane,
            "risk_level": risk_level, "delay_probability_pct": min(base_risk, 95),
            "risk_flags": flags, "intelligence_used": context[:2],
            "recommendation": "Safe to proceed" if risk_level == "LOW" else ("Proceed with caution" if risk_level == "MEDIUM" else "Do not use on this lane"),
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def RAGQueryTool(query: str) -> str:
    """
    Searches the FAISS vector store for procurement intelligence.
    Arguments:
    - query: A search term or question about logistics, carriers, or lanes.
    """
    try:
        results = query_rag(query, k=5)
        return json.dumps({"status": "success", "query": query, "results": results, "result_count": len(results)})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def RFQGeneratorTool(
    origin: str, 
    destination: str, 
    cargo_type: str = "General", 
    weight_kg: float = 1000,
    volume_cbm: float = 5.0,
    pickup_date: str = "TBD",
    delivery_deadline: str = "TBD",
    special_requirements: str = "None"
) -> str:
    """
    Generates a complete RFQ document text based on procurement details.
    """
    try:
        p = {
            "origin": origin, "destination": destination, "cargo_type": cargo_type, 
            "weight_kg": weight_kg, "volume_cbm": volume_cbm, 
            "pickup_date": pickup_date, "delivery_deadline": delivery_deadline,
            "special_requirements": special_requirements
        }
        rfq = f"""REQUEST FOR QUOTATION (RFQ)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RFQ Reference: RFQ-{datetime.now().strftime('%Y%m%d%H%M%S')}
Date of Issue: {datetime.now().strftime('%d %B %Y')}
Validity: 7 days from date of issue

SECTION 1 — LANE DETAILS
Origin: {p.get('origin','Mumbai')} | Destination: {p.get('destination','Delhi')}
Cargo Type: {p.get('cargo_type','General Cargo')}
Weight: {p.get('weight_kg',1000)} kg | Volume: {p.get('volume_cbm',5)} CBM
Pickup Date: {p.get('pickup_date','TBD')} | Delivery Deadline: {p.get('delivery_deadline','TBD')}
Special Requirements: {p.get('special_requirements','None')}

SECTION 2 — SLA CLAUSES
3.1 On-Time Delivery: Minimum 95% on-time delivery rate required per month.
3.2 POD Submission: Digital POD must be submitted within 24 hours of delivery.
3.3 Damage Limit: Damage claims exceeding 0.5% of shipment value monthly will attract penalty clauses.
3.4 GPS Tracking: Real-time GPS tracking mandatory for all shipments above 500 kg.
3.5 Insurance: Carrier must provide all-risk cargo insurance at carrier's cost.

SECTION 3 — PENALTY CONDITIONS
4.1 Late Delivery: Rs.500 per hour delay beyond committed transit time.
4.2 Damage: Full replacement cost of damaged goods at invoice value.
4.3 Fake POD: Contract termination + Rs.50,000 per incident penalty.

SECTION 4 — PAYMENT TERMS
5.1 Payment Cycle: 30 days from receipt of valid invoice + POD.
5.2 Invoice Format: GST-compliant invoice mandatory (GSTIN required).
5.3 TDS: TDS @ 2% will be deducted at source as applicable.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        return json.dumps({"status": "success", "rfq_text": rfq.strip()})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def AwardLetterTool(
    carrier_name: str, 
    lane: str, 
    rate: float, 
    sla_terms: str = "As per RFQ specifications",
    effective_date: str = "Immediately"
) -> str:
    """
    Generates a formal carrier award letter text.
    """
    try:
        p = {
            "carrier_name": carrier_name, "lane": lane, 
            "rate": rate, "sla_terms": sla_terms, 
            "effective_date": effective_date
        }
        ref = f"AWARD-{datetime.now().strftime('%Y%m%d')}-{p.get('carrier_name','')[:4].upper()}"
        letter = f"""AWARD LETTER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reference No.: {ref}
Date: {datetime.now().strftime('%d %B %Y')}

To: {p.get('carrier_name','Carrier Name')}

Subject: Award of Freight Contract — {p.get('lane','Lane')}

Lane: {p.get('lane','N/A')}
Contracted Rate: Rs.{p.get('rate',0):,.0f} per shipment (inclusive of GST)
Effective Date: {p.get('effective_date','Immediately')}
SLA Terms: {p.get('sla_terms','As per RFQ specifications')}

1. Minimum on-time delivery rate: 95% per month
2. GPS tracking mandatory from Day 1
3. Digital POD within 24 hours of delivery
4. Cargo insurance certificate before first shipment

Quarterly performance review. This contract is subject to termination with 30-day notice
if SLA targets are missed for two consecutive quarters.

Yours sincerely,
_____________________________
Procurement Head
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        return json.dumps({"status": "success", "award_letter": letter.strip()})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def FraudDetectorTool(carrier_name: str, billing_discrepancy_pct: float = 0, pod_disputes: int = 0, route_deviations: int = 0) -> str:
    """
    Analyzes carrier behavior patterns for fraud signals.
    """
    try:
        carrier = carrier_name
        fraud_context = query_rag(f"{carrier} fraud overbilling fake POD route deviation", k=3)
        flags = []
        risk_score = 0
        billing_disc = billing_discrepancy_pct or 0
        pod_disputes = pod_disputes or 0
        route_devs = route_deviations or 0
        if billing_disc > 5: flags.append(f"Overbilling: {billing_disc}% discrepancy"); risk_score += 25
        if pod_disputes > 2: flags.append(f"Multiple POD disputes: {pod_disputes}"); risk_score += 30
        if route_devs > 1: flags.append(f"Route deviations: {route_devs}"); risk_score += 20
        for ctx in fraud_context:
            if carrier.lower() in ctx.lower(): risk_score += 15; break
        risk_level = "LOW" if risk_score < 20 else ("MEDIUM" if risk_score < 50 else "HIGH")
        return json.dumps({
            "status": "success", "carrier": carrier,
            "fraud_risk_level": risk_level, "fraud_risk_score": min(risk_score, 100),
            "flags": flags, "rag_intelligence": fraud_context[:2],
            "recommendation": "Proceed normally" if risk_level == "LOW" else ("Audit next 3 shipments" if risk_level == "MEDIUM" else "Do NOT award new contracts"),
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@tool
def SeasonalPredictorTool(carrier_name: str, lane: str, target_month: str = "November") -> str:
    """
    Predicts seasonal reliability drops for a carrier or lane.
    """
    try:
        carrier = carrier_name
        lane = lane
        month = target_month or "November"
        context = query_rag(f"{carrier} {lane} seasonal performance {month}", k=3)
        high_risk = {"november": ("Festive season overload", 15), "december": ("Year-end surge", 12), "july": ("Monsoon", 18), "august": ("Peak monsoon", 20)}
        risk_info = high_risk.get(month.lower(), ("Normal operations", 0))
        return json.dumps({
            "status": "success", "carrier": carrier, "lane": lane, "target_month": month,
            "predicted_reliability_drop_pct": risk_info[1],
            "risk_reason": risk_info[0],
            "rag_evidence": context[:2],
            "warning": f"Reliability may drop ~{risk_info[1]}% in {month} due to {risk_info[0]}" if risk_info[1] > 0 else "No significant seasonal risk",
            "backup_recommendation": "Pre-book Rivigo or BlueDart as backup" if risk_info[1] > 10 else "No backup required",
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


# ─── Tool Registry ────────────────────────────────────────────────────────────

TOOLS = [
    BidNormalizerTool, CarrierScorerTool, RiskPredictorTool, RAGQueryTool,
    RFQGeneratorTool, AwardLetterTool, FraudDetectorTool, SeasonalPredictorTool,
]

TOOL_MAP = {t.name: t for t in TOOLS}

SYSTEM_PROMPT = """You are CarrierIQ, an AI-powered procurement co-pilot for logistics teams in India.
Your goal is to help users make better shipping decisions using your specialized tools.

GUIDELINES:
1. ALWAYS use tools to get real data. Never hallucinate carrier names or rates.
2. If asked about recommendations or risks for a lane (e.g., 'Mumbai to Delhi'), FIRST use RAGQueryTool to get intelligence.
3. Use reasoning to explain why you chose a specific tool or recommendation.
4. If a tool call fails, explain why and ask for missing information if needed.
5. All price values are in Indian Rupees (INR).
6. When calling tools, you MUST provide all required parameters in a single tool call.
"""


def get_llm_with_tools() -> Optional[object]:
    """Returns a ChatGroq instance with tools bound if API key is configured."""
    if not settings.groq_api_key or settings.groq_api_key == "your_groq_api_key_here":
        # Fallback to OpenAI if Groq not provided but OpenAI is
        if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=settings.openai_api_key)
                return llm.bind_tools(TOOLS)
            except: pass
        return None
    try:
        # Using Llama 3.1 8B on Groq for reliable tool calling
        llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, groq_api_key=settings.groq_api_key)
        return llm.bind_tools(TOOLS)
    except Exception as e:
        logger.error(f"Failed to create Groq LLM: {e}")
        return None


async def run_agent(query: str) -> Dict:
    """
    Run the LangChain agent with tool calling loop.
    Falls back to RAG-only if no OpenAI key.
    """
    llm_with_tools = get_llm_with_tools()
    if not llm_with_tools:
        return {"output": None, "error": "No Groq API key configured"}

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=query),
    ]

    max_iterations = 5
    for i in range(max_iterations):
        try:
            response = await llm_with_tools.ainvoke(messages)
            messages.append(response)

            if not response.tool_calls:
                return {"output": response.content, "iterations": i + 1}

            # Execute tool calls
            for tc in response.tool_calls:
                tool_name = tc["name"]
                tool_args = tc["args"]
                
                tool_fn = TOOL_MAP.get(tool_name)
                if tool_fn:
                    try:
                        # Use call directly for multi-arg tools
                        result = tool_fn.invoke(tool_args)
                    except Exception as e:
                        result = json.dumps({"error": str(e)})
                else:
                    result = json.dumps({"error": f"Tool {tool_name} not found"})

                messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

        except Exception as e:
            logger.error(f"Agent iteration {i} error: {e}")
            return {"output": None, "error": str(e)}

    # Return last AI message if we hit max iterations
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return {"output": msg.content, "iterations": max_iterations}

    return {"output": None, "error": "Max iterations reached"}


def run_tool_directly(tool_name: str, input_data: Any) -> Dict:
    """Run a specific tool without the full agent (for direct API calls)."""
    tool_fn = TOOL_MAP.get(tool_name)
    if not tool_fn:
        return {"error": f"Tool {tool_name} not found"}
    try:
        # Pass input_data directly to the Langchain tool instead of converting to a JSON string
        result = tool_fn.invoke(input_data)
        return json.loads(result) if isinstance(result, str) else result
    except Exception as e:
        return {"error": str(e)}
