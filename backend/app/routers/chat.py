from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models import Repository, QueryLog
from app.services.retrieval import retrieve_context, keyword_search
from app.services.llm import generate_chat_response

router = APIRouter(prefix="/repos", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []

class ChatResponse(BaseModel):
    answer: str
    citations: List[dict]

@router.post("/{repo_id}/chat", response_model=ChatResponse)
async def chat(repo_id: int, req: ChatRequest, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=400, detail="Repository not ready")

    contexts = await retrieve_context(repo_id, req.message, db, top_k=8)
    if not contexts:
        contexts = []

    # Add keyword matches as extra context
    kw = keyword_search(repo_id, req.message, db, top_k=5)
    citations = [{"file_path": c["file_path"], "chunk_index": c["chunk_index"]} for c in contexts]
    for k in kw:
        if not any(c["file_path"] == k["file_path"] for c in citations):
            citations.append({"file_path": k["file_path"], "language": k["language"]})

    answer = await generate_chat_response(req.message, contexts, req.history or [])

    log = QueryLog(repository_id=repo_id, query_text=req.message, response_text=answer, retrieved_chunks=citations)
    db.add(log)
    db.commit()

    return {"answer": answer, "citations": citations}

@router.get("/{repo_id}/chat/history")
def chat_history(repo_id: int, db: Session = Depends(get_db)):
    logs = db.query(QueryLog).filter(QueryLog.repository_id == repo_id).order_by(QueryLog.created_at.desc()).limit(50).all()
    return [
        {
            "id": log.id,
            "query": log.query_text,
            "response": log.response_text,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
