import asyncio
import httpx
from app.config import get_settings

async def test_exact():
    settings = get_settings()
    texts = ["Hello RepoLens AI"]
    payload = {"input": texts, "model": settings.EMBEDDING_MODEL}
    
    # Check what indexer.py does:
    if "e5" in settings.EMBEDDING_MODEL.lower() or "nemotron-embed" in settings.EMBEDDING_MODEL.lower():
        payload["input_type"] = "passage"
        
    print("Payload to send:", payload)
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.OPENAI_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json=payload,
            timeout=20.0,
        )
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print("Success!")
        else:
            print("Failed! Response:", resp.text)

if __name__ == "__main__":
    asyncio.run(test_exact())
