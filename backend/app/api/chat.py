import json
from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.database import get_db
from app.models.schemas import ChatQuery
from app.agents.master_agent import run_agent, run_tool_directly
from app.rag.rag_engine import query_rag
from app.config import settings

router = APIRouter(prefix="/chat", tags=["Procurement Chat"])


@router.post("")
async def chat_query(query: ChatQuery):
    """RAG-powered procurement chat. Returns intelligent ranked answers."""
    db = get_db()
    start_time = datetime.utcnow()

    # Retrieve RAG context first
    rag_results = query_rag(query.query, k=5)

    answer = ""
    reasoning = ""
    sources = []

    # Try full LangChain agent if key available
    try:
        agent_result = await run_agent(query.query)
        if agent_result.get("output"):
            answer = agent_result["output"]
            reasoning = f"Generated using LangChain tool-calling agent with GPT-4o + FAISS RAG ({agent_result.get('iterations',1)} iterations)"
            sources = rag_results[:3]
        else:
            answer = None
    except Exception as e:
        answer = None  # Fall through to smart fallback

    if not answer:
        # Smart rule-based + RAG fallback
        answer, reasoning = _smart_fallback(query.query, rag_results)
        sources = rag_results[:3]

    # Save to chat history
    chat_doc = {
        "user_id": query.user_id,
        "query": query.query,
        "answer": answer,
        "reasoning": reasoning,
        "sources": sources,
        "timestamp": start_time,
    }
    await db.chat_history.insert_one(chat_doc)

    return {
        "answer": answer,
        "reasoning": reasoning,
        "sources": sources,
        "timestamp": start_time.isoformat(),
    }


def _smart_fallback(query: str, rag_context: list) -> tuple:
    """Generate a smart answer from RAG context without LLM."""
    q_lower = query.lower()
    context_text = "\n".join(rag_context)

    if "best carrier" in q_lower or "recommend" in q_lower:
        # Extract carrier mentions from context
        carriers = ["BlueDart", "Rivigo", "Delhivery", "DTDC", "Gati", "TCI", "Safexpress", "XpressBees"]
        mentioned = [c for c in carriers if c.lower() in context_text.lower()]
        if mentioned:
            answer = (
                f"**Based on procurement intelligence database analysis:**\n\n"
                f"🏆 **Top Recommendation: {mentioned[0]}**\n\n"
                f"Key findings from carrier knowledge base:\n"
            )
            for chunk in rag_context[:3]:
                if any(m.lower() in chunk.lower() for m in mentioned[:2]):
                    answer += f"• {chunk[:150]}...\n"
            reasoning = f"Answer generated via FAISS semantic search. Matched {len(mentioned)} carriers in knowledge base. Enable OpenAI API key for full LLM-powered analysis."
        else:
            answer = f"**Intelligence Search Results:**\n\n" + "\n\n".join([f"• {r[:200]}" for r in rag_context[:3]])
            reasoning = "RAG keyword search used. For full conversational AI, configure OpenAI API key."
    elif "fraud" in q_lower or "risk" in q_lower:
        fraud_chunks = [r for r in rag_context if "fraud" in r.lower() or "risk" in r.lower()]
        answer = "**⚠️ Risk & Fraud Intelligence:**\n\n" + "\n\n".join([f"• {r[:200]}" for r in (fraud_chunks or rag_context)[:3]])
        reasoning = "Fraud intelligence retrieved from carrier knowledge base via RAG search."
    elif "benchmark" in q_lower or "rate" in q_lower or "overpay" in q_lower:
        bench_chunks = [r for r in rag_context if "benchmark" in r.lower() or "rate" in r.lower()]
        answer = "**💰 Market Rate Intelligence:**\n\n" + "\n\n".join([f"• {r[:200]}" for r in (bench_chunks or rag_context)[:3]])
        reasoning = "Benchmark data retrieved from market intelligence knowledge base."
    else:
        answer = "**Procurement Intelligence:**\n\n" + "\n\n".join([f"• {r[:200]}" for r in rag_context[:3]])
        reasoning = "Results retrieved from CarrierIQ knowledge base via semantic search."

    return answer, reasoning


@router.get("/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 20):
    """Retrieve conversation history for a user."""
    db = get_db()
    history = await db.chat_history.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).to_list(limit)
    for h in history:
        h["_id"] = str(h["_id"])
        if "timestamp" in h:
            h["timestamp"] = h["timestamp"].isoformat() if hasattr(h["timestamp"], "isoformat") else str(h["timestamp"])
    return {"history": history}
