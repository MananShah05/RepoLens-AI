import asyncio
import httpx
from app.config import get_settings

async def list_models():
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.OPENAI_BASE_URL}/models",
                headers=headers,
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                models = [m["id"] for m in data.get("data", [])]
                print("Available Nvidia NIM Models:")
                for m in sorted(models):
                    print(f"- {m}")
            else:
                print(f"Failed: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
