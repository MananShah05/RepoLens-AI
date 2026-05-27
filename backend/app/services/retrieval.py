from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.indexer import get_collection
from app.models import Chunk, File
import os

async def retrieve_context(repo_id: int, query: str, db: Session, top_k: int = 8) -> List[Dict[str, Any]]:
    from app.services.indexer import get_embedding
    
    contexts = []
    try:
        collection = get_collection(repo_id)
        embeddings = await get_embedding([query], input_type="query")
        results = collection.query(query_embeddings=embeddings, n_results=top_k)

        if results and results.get("ids"):
            ids = results["ids"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]

            # Batch-fetch all chunks and files in 2 queries instead of 2*N
            chunk_ids = [int(doc_id.replace("chunk_", "")) for doc_id in ids]
            file_ids = list({meta["file_id"] for meta in metadatas})

            chunks_by_id = {c.id: c for c in db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()} if chunk_ids else {}
            files_by_id = {f.id: f for f in db.query(File).filter(File.id.in_(file_ids)).all()} if file_ids else {}

            for doc_id, doc, meta in zip(ids, documents, metadatas):
                chunk_id = int(doc_id.replace("chunk_", ""))
                file_obj = files_by_id.get(meta["file_id"])
                contexts.append({
                    "chunk_id": chunk_id,
                    "content": doc,
                    "file_path": file_obj.path if file_obj else "",
                    "file_id": file_obj.id if file_obj else None,
                    "chunk_index": meta.get("chunk_index", 0),
                })
    except Exception as e:
        print(f"Warning: Vector retrieval failed ({e}). Falling back to keyword search.")
        # Fallback to enhanced keyword search
        keyword_results = keyword_search(repo_id, query, db, top_k=top_k)
        for kr in keyword_results:
            contexts.append({
                "chunk_id": kr["chunk_id"],
                "content": kr["content"],
                "file_path": kr["file_path"],
                "file_id": kr["file_id"],
                "chunk_index": kr["chunk_index"],
            })
            
    return contexts

def keyword_search(repo_id: int, query: str, db: Session, top_k: int = 10) -> List[Dict[str, Any]]:
    # Robust keyword search inside chunk contents & file paths
    query_lower = query.lower()
    chunks = db.query(Chunk).join(File).filter(File.repository_id == repo_id).all()
    
    results = []
    for c in chunks:
        score = 0
        # Check term frequency in chunk content
        if query_lower in c.content.lower():
            score += c.content.lower().count(query_lower)
        # Check path matches
        if query_lower in c.file.path.lower():
            score += 10
            
        if score > 0:
            results.append({
                "chunk_id": c.id,
                "content": c.content,
                "file_path": c.file.path,
                "file_id": c.file.id,
                "chunk_index": c.chunk_index,
                "language": c.file.language,
                "score": score,
            })
            
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
