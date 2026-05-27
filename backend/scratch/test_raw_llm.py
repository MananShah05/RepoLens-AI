import asyncio
import httpx
from app.config import get_settings

async def test_llm():
    settings = get_settings()
    print(f"URL: {settings.OPENAI_BASE_URL}")
    print(f"Model: {settings.CHAT_MODEL}")
    print("Sending simple completion request...")
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers=headers,
                json={
                    "model": settings.CHAT_MODEL,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "temperature": 0.3,
                    "stream": False,
                },
                timeout=30.0,
            )
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                print("SUCCESS!")
                print(resp.json())
            else:
                print(f"FAILED: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())
