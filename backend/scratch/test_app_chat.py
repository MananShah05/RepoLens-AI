import asyncio
import httpx

async def test_chat():
    url = "http://127.0.0.1:8000/repos/5/chat"
    payload = {
        "message": "What does this repo do?",
        "history": []
    }
    print(f"Sending chat request to: {url}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=60.0)
            print(f"Status Code: {resp.status_code}")
            if resp.status_code == 200:
                print("SUCCESS!")
                print(resp.json())
            else:
                print(f"FAILED: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
