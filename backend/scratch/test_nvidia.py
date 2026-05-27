import asyncio
import httpx
from app.config import get_settings

async def test_embeddings():
    settings = get_settings()
    print("Testing NVIDIA Embeddings API...")
    print(f"Base URL: {settings.OPENAI_BASE_URL}")
    print(f"Key Prefix: {settings.OPENAI_API_KEY[:10]}...")
    print(f"Model: {settings.EMBEDDING_MODEL}")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.OPENAI_BASE_URL}/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={"input": ["Hello RepoLens AI!"], "model": settings.EMBEDDING_MODEL},
                timeout=20.0,
            )
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                emb = data["data"][0]["embedding"]
                print(f"Success! Generated embedding of length: {len(emb)}")
                print(f"First 5 values: {emb[:5]}")
            else:
                print(f"Failed! Response: {resp.text}")
        except Exception as e:
            print(f"Error testing embeddings: {e}")

async def test_chat():
    settings = get_settings()
    print("\nTesting NVIDIA Chat API...")
    print(f"Model: {settings.CHAT_MODEL}")
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": settings.CHAT_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Say hello in one short sentence."}
                    ],
                    "temperature": 0.3,
                },
                timeout=30.0,
            )
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                ans = data["choices"][0]["message"]["content"]
                print(f"Success! Chat Response:\n{ans}")
            else:
                print(f"Failed! Response: {resp.text}")
        except Exception as e:
            print(f"Error testing chat: {e}")

if __name__ == "__main__":
    asyncio.run(test_embeddings())
    asyncio.run(test_chat())
