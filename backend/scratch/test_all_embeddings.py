import asyncio
import httpx
from app.config import get_settings

async def test_models():
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        # Test nv-embedqa-e5-v5 with input_type
        print("\nTesting nvidia/nv-embedqa-e5-v5 with input_type='query'...")
        try:
            resp = await client.post(
                f"{settings.OPENAI_BASE_URL}/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"input": ["Hello"], "model": "nvidia/nv-embedqa-e5-v5", "input_type": "query"},
                timeout=20.0,
            )
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                emb = data["data"][0]["embedding"]
                print(f"SUCCESS! Dimension: {len(emb)}")
            else:
                print(f"FAILED: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

        # Test other models
        other_models = [
            "nvidia/llama-3.2-nv-embedqa-1b-v1",
            "nvidia/llama-nemotron-embed-1b-v2",
        ]
        for model in other_models:
            print(f"\nTesting {model}...")
            try:
                resp = await client.post(
                    f"{settings.OPENAI_BASE_URL}/embeddings",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={"input": ["Hello"], "model": model, "input_type": "query"},
                    timeout=20.0,
                )
                print(f"Status Code: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    emb = data["data"][0]["embedding"]
                    print(f"SUCCESS! Dimension: {len(emb)}")
                else:
                    print(f"FAILED: {resp.text}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_models())
