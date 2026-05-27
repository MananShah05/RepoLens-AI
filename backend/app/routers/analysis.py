import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models import Repository, File, Chunk, Diagram
from app.services.retrieval import retrieve_context, keyword_search
from app.services.llm import generate_summary, generate_architecture, generate_onboarding, explain_file
from app.services.diagram import build_dependency_graph, save_or_update_diagram
from app.config import get_settings

router = APIRouter(prefix="/repos", tags=["analysis"])

class AnalyzeRequest(BaseModel):
    pass

@router.post("/{repo_id}/analyze")
def trigger_analysis(repo_id: int, db: Session = Depends(get_db)):
    # Analysis is triggered during ingestion already, but allow re-trigger
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"status": repo.status}

@router.get("/{repo_id}/summary")
async def get_summary(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=400, detail="Repository not ready")

    settings = get_settings()
    cache_path = os.path.join(settings.CLONE_DIR, str(repo_id), "summary.md")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.startswith("*AI Generation Error*"):
                    return {"summary": content}
        except Exception:
            pass

    chunks = db.query(Chunk).join(File).filter(File.repository_id == repo_id).limit(30).all()
    context = [{"file_path": c.file.path, "content": c.content} for c in chunks]
    summary = await generate_summary(context)

    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(summary)
    except Exception:
        pass

    return {"summary": summary}

@router.get("/{repo_id}/architecture")
async def get_architecture(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=400, detail="Repository not ready")

    settings = get_settings()
    cache_path = os.path.join(settings.CLONE_DIR, str(repo_id), "architecture.md")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.startswith("*AI Generation Error*"):
                    return {"architecture": content}
        except Exception:
            pass

    chunks = db.query(Chunk).join(File).filter(File.repository_id == repo_id).limit(30).all()
    context = [{"file_path": c.file.path, "content": c.content} for c in chunks]
    arch = await generate_architecture(context)

    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(arch)
    except Exception:
        pass

    return {"architecture": arch}

@router.get("/{repo_id}/onboarding")
async def get_onboarding(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=400, detail="Repository not ready")

    settings = get_settings()
    cache_path = os.path.join(settings.CLONE_DIR, str(repo_id), "onboarding_guide.md")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.startswith("*AI Generation Error*"):
                    return {"guide": content}
        except Exception:
            pass

    # Prioritize readme, package files, config files
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

    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(guide)
    except Exception:
        pass

    return {"guide": guide}

@router.get("/{repo_id}/graph")
def get_graph(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    diag = db.query(Diagram).filter(Diagram.repository_id == repo_id, Diagram.type == "dependency").first()
    if not diag:
        mermaid = build_dependency_graph(repo_id, db)
        diag = save_or_update_diagram(repo_id, "dependency", mermaid, db)
    return {"type": diag.type, "payload": diag.payload}

@router.post("/{repo_id}/diagram/regenerate")
def regenerate_graph(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    mermaid = build_dependency_graph(repo_id, db)
    diag = save_or_update_diagram(repo_id, "dependency", mermaid, db)
    return {"type": diag.type, "payload": diag.payload}

@router.get("/{repo_id}/files/{file_id}/explain")
async def explain_file_endpoint(repo_id: int, file_id: int, db: Session = Depends(get_db)):
    f = db.query(File).filter(File.id == file_id, File.repository_id == repo_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    explanation = await explain_file(f.path, f.content_preview or "")
    return {"explanation": explanation}
