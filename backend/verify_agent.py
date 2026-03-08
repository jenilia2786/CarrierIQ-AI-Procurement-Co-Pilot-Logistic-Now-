import sys
import os
import asyncio
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agents.master_agent import run_agent, TOOLS
from app.config import settings

async def verify():
    print("=== CarrierIQ Agent Verification ===")
    
    # 1. Check Tools
    print(f"[*] Registered Tools: {[t.name for t in TOOLS]}")
    
    # 2. Check API Key
    has_groq = settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here"
    has_openai = settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here"
    print(f"[*] Groq API Key configured: {has_groq}")
    print(f"[*] OpenAI API Key configured: {has_openai}")
    
    # 3. Test Agent Flow (Mocked if no key)
    query = "Recommend a carrier for Mumbai to Delhi"
    print(f"[*] Testing query: '{query}'")
    
    try:
        result = await run_agent(query)
        if result.get("output"):
            print(f"[OK] Real Agent Output: {result['output'][:100]}...")
        else:
            print(f"[WARN] Real Agent failed (likely missing key or error). Fallback will be used.")
            print(f"   Error detail: {result.get('error')}")
    except Exception as e:
        print(f"[ERROR] Agent execution error: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
