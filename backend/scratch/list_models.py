import asyncio
import httpx
from app.config import get_settings

async def list_models():
    settings = get_settings()
    print("Listing NVIDIA models...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{settings.OPENAI_BASE_URL}/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                timeout=20.0,
            )
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["id"] for m in data.get("data", [])]
                print(f"Total models found: {len(models)}")
                
                # Search for mistral models
                mistral_models = [m for m in models if "mistral" in m.lower()]
                print("\nMistral models:")
                for m in mistral_models:
                    print(f" - {m}")
                    
                print("\nAll models:")
                for m in sorted(models):
                    print(f" - {m}")
            else:
                print(f"Failed! Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
