import asyncio
import os
import sys

# Adjust import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Repository, File, Chunk
from app.services.llm import generate_onboarding, generate_summary, generate_architecture
from app.config import get_settings

async def pregenerate_all():
    db = SessionLocal()
    try:
        repo_id = 5
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            print(f"Repository {repo_id} not found in DB!")
            return
        print(f"Repository: {repo.name}, Status: {repo.status}")
        
        settings = get_settings()
        clone_dir = settings.CLONE_DIR
        
        # 1. Onboarding Guide
        print("Generating Onboarding Guide...")
        priority_paths = ["readme", "package.json", "requirements.txt", "pyproject.toml", "dockerfile", ".env", "docker-compose"]
        files = db.query(File).filter(File.repository_id == repo_id).all()
        selected = []
        for f in files:
            lower = f.path.lower()
            if any(p in lower for p in priority_paths):
                selected.append(f)
        if len(selected) < 10:
            selected += [f for f in files if f not in selected][:20]
        chunks = db.query(Chunk).filter(Chunk.file_id.in_([f.id for f in selected])).limit(10).all()
        context = [{"file_path": c.file.path, "content": c.content} for c in chunks]
        
        guide = await generate_onboarding(context)
        cache_path = os.path.join(clone_dir, str(repo_id), "onboarding_guide.md")
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(guide)
        print(f"Successfully cached onboarding guide to {cache_path}")
        
        # 2. Summary
        print("Generating Summary...")
        all_chunks = db.query(Chunk).join(File).filter(File.repository_id == repo_id).limit(20).all()
        summary_context = [{"file_path": c.file.path, "content": c.content} for c in all_chunks]
        
        summary = await generate_summary(summary_context)
        summary_cache_path = os.path.join(clone_dir, str(repo_id), "summary.md")
        with open(summary_cache_path, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"Successfully cached summary to {summary_cache_path}")
        
        # 3. Architecture
        print("Generating Architecture Overview...")
        arch = await generate_architecture(summary_context)
        arch_cache_path = os.path.join(clone_dir, str(repo_id), "architecture.md")
        with open(arch_cache_path, "w", encoding="utf-8") as f:
            f.write(arch)
        print(f"Successfully cached architecture overview to {arch_cache_path}")
        
        print("\nAll AI artifacts pre-generated successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(pregenerate_all())
