import asyncio
import sys
import os

# Adjust import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Repository, File, Chunk
from app.services.llm import generate_onboarding

async def test_onboarding():
    db = SessionLocal()
    try:
        repo_id = 5
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            print(f"Repository {repo_id} not found in DB!")
            return
        print(f"Repository: {repo.name}, Status: {repo.status}")
        
        priority_paths = ["readme", "package.json", "requirements.txt", "pyproject.toml", "dockerfile", ".env", "docker-compose"]
        files = db.query(File).filter(File.repository_id == repo_id).all()
        selected = []
        for f in files:
            lower = f.path.lower()
            if any(p in lower for p in priority_paths):
                selected.append(f)
        if len(selected) < 10:
            selected += [f for f in files if f not in selected][:20]
        
        print(f"Found {len(files)} total files, selected {len(selected)} priority/sample files.")
        
        chunks = db.query(Chunk).filter(Chunk.file_id.in_([f.id for f in selected])).limit(5).all()
        print(f"Found {len(chunks)} chunks.")
        
        context = [{"file_path": c.file.path, "content": c.content} for c in chunks]
        
        print("Calling generate_onboarding...")
        import time
        start_time = time.time()
        guide = await generate_onboarding(context)
        end_time = time.time()
        print(f"generate_onboarding completed in {end_time - start_time:.2f} seconds.")
        print("RESULT (writing to guide_output.txt):")
        with open("guide_output.txt", "w", encoding="utf-8") as f:
            f.write(guide)
        print("Successfully wrote guide to guide_output.txt")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_onboarding())
