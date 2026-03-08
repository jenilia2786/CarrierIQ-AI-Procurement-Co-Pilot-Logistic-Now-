import json
from app.api.carriers import upload_bids
import asyncio

async def test():
    ret = await upload_bids(None, None, "demo")
    print("RETURN:", json.dumps(ret, indent=2))

asyncio.run(test())
