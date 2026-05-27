import asyncio
import httpx
import os
import sys

# Adjust import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import get_settings

async def main():
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
    }
    async with httpx.AsyncClient() as client:
        # 1. List models
        print("Fetching models from NVIDIA API...")
        try:
            resp = await client.get(f"{settings.OPENAI_BASE_URL}/models", headers=headers)
            print(f"Models response status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["id"] for m in data.get("data", [])]
                print(f"Total models: {len(models)}")
                print("Available models:")
                for m in sorted(models):
                    print(f" - {m}")
            else:
                print(f"Failed to fetch models: {resp.text}")
        except Exception as e:
            print(f"Error fetching models: {e}")

        # 2. Test completion with CHAT_MODEL
        print(f"\nTesting chat completion with current CHAT_MODEL: {settings.CHAT_MODEL}...")
        try:
            resp = await client.post(
                f"{settings.OPENAI_BASE_URL}/chat/completions",
                headers=headers,
                json={
                    "model": settings.CHAT_MODEL,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "temperature": 0.3,
                },
                timeout=10.0
            )
            print(f"Completion status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"Completion succeeded: {resp.json()['choices'][0]['message']['content']}")
            else:
                print(f"Completion failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Error in completion: {e}")

        # Try alternative models
        test_models = [
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "meta/llama-3.3-70b-instruct",
            "mistralai/mistral-large-2-instruct",
        ]
        for model in test_models:
            print(f"\nTesting alternative model: {model}...")
            try:
                resp = await client.post(
                    f"{settings.OPENAI_BASE_URL}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Hello"}],
                        "temperature": 0.3,
                    },
                    timeout=10.0
                )
                print(f"Status for {model}: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"Succeeded! First 50 chars of response: {resp.json()['choices'][0]['message']['content'][:50]}")
                else:
                    print(f"Failed: {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
