from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
from app.database import get_db
from app.models import Repository, File, Symbol, Chunk, Diagram, QueryLog
from app.services.ingestion import clone_repository, scan_files, update_repo_status
from app.services.parser import parse_file
from app.services.indexer import index_chunks, delete_repo_index
from app.services.diagram import build_dependency_graph, build_file_tree, save_or_update_diagram
from app.config import get_settings
import os
import shutil
import asyncio
import logging

import stat

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repos", tags=["repositories"])

class ImportRepoRequest(BaseModel):
    github_url: str
    branch: Optional[str] = None

class RepoOut(BaseModel):
    id: int
    github_url: str
    name: str
    owner: str
    default_branch: str
    status: str
    status_message: str
    language_summary: Any
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/import", response_model=RepoOut)
def import_repo(req: ImportRepoRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    repo, clone_dir = clone_repository(db, req.github_url, req.branch)
    background_tasks.add_task(ingest_pipeline, repo.id, clone_dir)
    return repo

@router.get("", response_model=List[RepoOut])
def list_repos(db: Session = Depends(get_db)):
    return db.query(Repository).order_by(Repository.created_at.desc()).all()

@router.get("/{repo_id}", response_model=RepoOut)
def get_repo(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@router.get("/{repo_id}/status")
def repo_status(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"status": repo.status, "message": repo.status_message}

@router.delete("/{repo_id}")
def delete_repo(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Remove cloned files from disk
    settings = get_settings()
    clone_dir = os.path.join(settings.CLONE_DIR, f"{repo.owner}_{repo.name}")
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir, onerror=remove_readonly)

    # Remove vector index
    try:
        delete_repo_index(repo_id)
    except Exception as e:
        logger.warning(f"Failed to delete vector index for repo {repo_id}: {e}")

    # Explicitly delete child records in dependency order to avoid
    # cascade issues and orphaned rows from concurrent ingestion.
    file_ids = [f.id for f in db.query(File.id).filter(File.repository_id == repo_id).all()]
    if file_ids:
        db.query(Chunk).filter(Chunk.file_id.in_(file_ids)).delete(synchronize_session=False)
        db.query(Symbol).filter(Symbol.file_id.in_(file_ids)).delete(synchronize_session=False)
    db.query(File).filter(File.repository_id == repo_id).delete(synchronize_session=False)
    db.query(Diagram).filter(Diagram.repository_id == repo_id).delete(synchronize_session=False)
    db.query(QueryLog).filter(QueryLog.repository_id == repo_id).delete(synchronize_session=False)
    db.query(Repository).filter(Repository.id == repo_id).delete(synchronize_session=False)
    db.commit()
    return {"ok": True}

@router.get("/{repo_id}/files")
def list_files(repo_id: int, db: Session = Depends(get_db)):
    files = db.query(File).filter(File.repository_id == repo_id).all()
    return [{"id": f.id, "path": f.path, "language": f.language, "size": f.size} for f in files]

@router.get("/{repo_id}/files/{file_id}")
def get_file(repo_id: int, file_id: int, db: Session = Depends(get_db)):
    f = db.query(File).filter(File.id == file_id, File.repository_id == repo_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    symbols = db.query(Symbol).filter(Symbol.file_id == file_id).all()
    return {
        "id": f.id,
        "path": f.path,
        "language": f.language,
        "size": f.size,
        "content_preview": f.content_preview,
        "symbols": [{"name": s.name, "type": s.symbol_type, "start_line": s.start_line, "end_line": s.end_line} for s in symbols],
    }

@router.get("/{repo_id}/tree")
def get_tree(repo_id: int, db: Session = Depends(get_db)):
    return build_file_tree(repo_id, db)

# Background ingestion pipeline
def ingest_pipeline(repo_id: int, clone_dir: str):
    """Run the full ingestion pipeline in a background task.

    Creates its own DB session since BackgroundTasks run after
    the request's session is closed.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            logger.error(f"Repository {repo_id} not found in background task")
            return

        # Step 1: Scan files
        files_added = scan_files(repo, clone_dir, db)
        update_repo_status(db, repo_id, "parsing", f"Parsing {len(files_added)} files...")

        # Step 2: Parse files in parallel
        from concurrent.futures import ThreadPoolExecutor
        from app.services.parser import parse_single_file_data

        settings = get_settings()
        max_chunk_size = settings.MAX_CHUNK_SIZE
        chunk_overlap = settings.CHUNK_OVERLAP

        # Map each file_obj to its parameters
        tasks = []
        for file_obj, filepath in files_added:
            tasks.append((file_obj.id, filepath, file_obj.language))

        max_workers = min(16, (os.cpu_count() or 4) * 2)
        parsed_results = {}

        def worker(task):
            file_id, filepath, language = task
            try:
                res = parse_single_file_data(filepath, language, max_chunk_size, chunk_overlap)
                return file_id, res
            except Exception as e:
                logger.warning(f"Error in parallel parsing of {filepath}: {e}")
                return file_id, {
                    "status": "error",
                    "hash": "",
                    "content_preview": "",
                    "symbols": [],
                    "chunks": []
                }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(worker, tasks))
            for file_id, res in results:
                parsed_results[file_id] = res

        # Step 2b: Update DB in bulk and commit once
        parsed = 0
        file_updates = []
        all_symbol_dicts = []
        all_chunk_dicts = []

        for file_id, res in parsed_results.items():
            content_preview = res.get("content_preview") or ""
            if isinstance(content_preview, str):
                content_preview = content_preview.replace("\x00", "")
            file_updates.append({
                "id": file_id,
                "parsed_status": res["status"],
                "hash": res["hash"],
                "content_preview": content_preview
            })

            if res["status"] == "parsed":
                parsed += 1
                for sym_data in res["symbols"]:
                    sym_name = sym_data.get("name") or ""
                    if isinstance(sym_name, str):
                        sym_name = sym_name.replace("\x00", "")
                    all_symbol_dicts.append({
                        "file_id": file_id,
                        "name": sym_name,
                        "symbol_type": sym_data["symbol_type"],
                        "start_line": sym_data["start_line"],
                        "end_line": sym_data["end_line"],
                    })

                for chunk_data in res["chunks"]:
                    chunk_content = chunk_data.get("content") or ""
                    if isinstance(chunk_content, str):
                        chunk_content = chunk_content.replace("\x00", "")
                    all_chunk_dicts.append({
                        "file_id": file_id,
                        "content": chunk_content,
                        "chunk_index": chunk_data["chunk_index"],
                        "hash": chunk_data["hash"],
                    })

        # Bulk update files and bulk insert symbols & chunks in batch statements
        if file_updates:
            db.bulk_update_mappings(File, file_updates)
        if all_symbol_dicts:
            db.bulk_insert_mappings(Symbol, all_symbol_dicts)
        if all_chunk_dicts:
            db.bulk_insert_mappings(Chunk, all_chunk_dicts)

        db.commit()

        # Step 3: Index chunks (async function — run in new event loop)
        update_repo_status(db, repo_id, "indexing", f"Indexing {parsed} parsed files...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(index_chunks(repo_id, db))
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"Indexing error (non-fatal): {e}")

        # Step 4: Generate dependency graph
        try:
            mermaid = build_dependency_graph(repo_id, db)
            save_or_update_diagram(repo_id, "dependency", mermaid, db)
        except Exception as e:
            logger.warning(f"Diagram generation error (non-fatal): {e}")

        # Step 5: Pre-generate onboarding, summary, and architecture cache in background
        update_repo_status(db, repo_id, "indexing", "Pre-generating AI onboarding guide & summaries...")
        try:
            from app.services.llm import generate_onboarding, generate_summary, generate_architecture
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # 1. Onboarding
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
                
                guide = loop.run_until_complete(generate_onboarding(context))
                cache_path = os.path.join(settings.CLONE_DIR, str(repo_id), "onboarding_guide.md")
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(guide)
                    
                # 2. Summary
                all_chunks = db.query(Chunk).join(File).filter(File.repository_id == repo_id).limit(20).all()
                summary_context = [{"file_path": c.file.path, "content": c.content} for c in all_chunks]
                summary = loop.run_until_complete(generate_summary(summary_context))
                summary_cache_path = os.path.join(settings.CLONE_DIR, str(repo_id), "summary.md")
                with open(summary_cache_path, "w", encoding="utf-8") as f:
                    f.write(summary)
                    
                # 3. Architecture
                arch = loop.run_until_complete(generate_architecture(summary_context))
                arch_cache_path = os.path.join(settings.CLONE_DIR, str(repo_id), "architecture.md")
                with open(arch_cache_path, "w", encoding="utf-8") as f:
                    f.write(arch)
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"AI Pre-generation error (non-fatal): {e}")

        update_repo_status(db, repo_id, "ready", "Repository analysis complete")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Ingestion pipeline failed for repo {repo_id}: {e}\n{tb}")
        try:
            db.rollback()
        except Exception:
            pass
        update_repo_status(db, repo_id, "error", str(e))
    finally:
        db.close()

