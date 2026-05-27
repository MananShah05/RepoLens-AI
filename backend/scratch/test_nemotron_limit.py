import asyncio
import httpx
from app.config import get_settings

async def main():
    settings = get_settings()
    # Create a long text of 4000 characters (approx 1000 tokens)
    long_text = "print('hello world')\n" * 200
    print("Length of long text:", len(long_text))
    
    async with httpx.AsyncClient() as client:
        # Test llama-nemotron-embed-1b-v2
        payload = {
            "input": [long_text],
            "model": "nvidia/llama-nemotron-embed-1b-v2",
            "input_type": "passage"
        }
        resp = await client.post(
            f"{settings.OPENAI_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json=payload,
            timeout=20.0,
        )
        print(f"Nemotron status code: {resp.status_code}")
        if resp.status_code != 200:
            print("Nemotron failed:", resp.text)
        else:
            print("Nemotron succeeded!")
            
        # Also test nv-embedqa-e5-v5 for comparison
        payload["model"] = "nvidia/nv-embedqa-e5-v5"
        resp = await client.post(
            f"{settings.OPENAI_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json=payload,
            timeout=20.0,
        )
        print(f"E5 status code: {resp.status_code}")
        if resp.status_code != 200:
            print("E5 failed:", resp.text)

if __name__ == "__main__":
    asyncio.run(main())
