import httpx
import time
import sys

base_url = "http://localhost:8000"

# Step 1: Clean up all existing repositories
try:
    print("Listing all repositories...")
    resp = httpx.get(f"{base_url}/repos", timeout=10.0)
    repos = resp.json()
    for r in repos:
        print(f"Deleting repository {r['id']}...")
        httpx.delete(f"{base_url}/repos/{r['id']}", timeout=10.0)
except Exception as e:
    print(f"Cleanup failed: {e}")

# Step 2: Import repository
repo_url = "https://github.com/MananShah05/transcend-frames"
print(f"Importing repository {repo_url}...")
try:
    resp = httpx.post(
        f"{base_url}/repos/import",
        json={"github_url": repo_url},
        timeout=15.0
    )
    resp.raise_for_status()
    repo_data = resp.json()
    new_id = repo_data["id"]
    print(f"Import started. New repository ID: {new_id}")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

# Step 3: Poll status
print("Polling repository status...")
start_time = time.time()
while True:
    try:
        resp = httpx.get(f"{base_url}/repos/{new_id}/status", timeout=5.0)
        resp.raise_for_status()
        status_data = resp.json()
        status = status_data["status"]
        msg = status_data["message"]
        print(f"[{time.time() - start_time:.1f}s] Status: {status} | Message: {msg}")
        
        if status in ("ready", "error"):
            print(f"Terminated with status: {status}")
            break
    except Exception as e:
        print(f"Polling failed: {e}")
        
    time.sleep(2)
