import asyncio
import time
import httpx

async def test_endpoints():
    base_url = "http://127.0.0.1:8000/repos/5"
    async with httpx.AsyncClient() as client:
        # Test Onboarding
        print("\nTesting GET /onboarding...")
        start = time.time()
        try:
            resp = await client.get(f"{base_url}/onboarding", timeout=10.0)
            elapsed = time.time() - start
            print(f"Status Code: {resp.status_code}")
            print(f"Time Taken: {elapsed:.4f} seconds")
            if resp.status_code == 200:
                guide = resp.json().get("guide", "")
                print(f"Content Length: {len(guide)} characters")
                print("First 100 characters of guide:")
                print(guide[:100].replace('\n', ' '))
            else:
                print(f"Failed: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

        # Test Summary
        print("\nTesting GET /summary...")
        start = time.time()
        try:
            resp = await client.get(f"{base_url}/summary", timeout=10.0)
            elapsed = time.time() - start
            print(f"Status Code: {resp.status_code}")
            print(f"Time Taken: {elapsed:.4f} seconds")
            if resp.status_code == 200:
                summary = resp.json().get("summary", "")
                print(f"Content Length: {len(summary)} characters")
                print("First 100 characters of summary:")
                print(summary[:100].replace('\n', ' '))
            else:
                print(f"Failed: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

        # Test Architecture
        print("\nTesting GET /architecture...")
        start = time.time()
        try:
            resp = await client.get(f"{base_url}/architecture", timeout=40.0)
            elapsed = time.time() - start
            print(f"Status Code: {resp.status_code}")
            print(f"Time Taken: {elapsed:.4f} seconds")
            if resp.status_code == 200:
                arch = resp.json().get("architecture", "")
                print(f"Content Length: {len(arch)} characters")
                print("First 100 characters of architecture:")
                print(arch[:100].replace('\n', ' '))
            else:
                print(f"Failed: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
