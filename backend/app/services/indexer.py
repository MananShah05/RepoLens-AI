import os
import httpx
from typing import List
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import Chunk, File
import chromadb
from chromadb.config import Settings as ChromaSettings

_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client

def get_collection(repo_id: int):
    client = get_chroma_client()
    return client.get_or_create_collection(f"repo_{repo_id}")

async def get_embedding(texts: List[str], input_type: str = None) -> List[List[float]]:
    settings = get_settings()
    # Resolve dimensions dynamically
    if "nv-embedqa-e5" in settings.EMBEDDING_MODEL.lower():
        dim = 1024
    elif "llama-nemotron-embed" in settings.EMBEDDING_MODEL.lower():
        dim = 2048
    elif "nv-embed" in settings.EMBEDDING_MODEL.lower():
        dim = 4096
    elif "nvidia" in settings.EMBEDDING_MODEL.lower():
        dim = 1024
    else:
        dim = 1536

    if not settings.OPENAI_API_KEY:
        # Return zero embeddings as fallback if no key
        return [[0.0] * dim for _ in texts]
    try:
        async with httpx.AsyncClient() as client:
            payload = {"input": texts, "model": settings.EMBEDDING_MODEL}
            
            # Asymmetric models require input_type
            if input_type:
                payload["input_type"] = input_type
            elif "e5" in settings.EMBEDDING_MODEL.lower() or "nemotron-embed" in settings.EMBEDDING_MODEL.lower():
                payload["input_type"] = "passage"

            resp = await client.post(
                f"{settings.OPENAI_BASE_URL}/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json=payload,
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            return [d["embedding"] for d in data]
    except Exception as e:
        print(f"Warning: Embedding generation failed ({e}). Falling back to zero-embeddings.")
        return [[0.0] * dim for _ in texts]

async def index_chunks(repo_id: int, db: Session):
    import asyncio
    settings = get_settings()
    collection = get_collection(repo_id)
    chunks = db.query(Chunk).join(File).filter(File.repository_id == repo_id).all()
    if not chunks:
        return

    batch_size = 32
    semaphore = asyncio.Semaphore(8)

    async def process_batch(batch):
        async with semaphore:
            texts = [c.content for c in batch]
            embeddings = await get_embedding(texts)
            ids = [f"chunk_{c.id}" for c in batch]
            metadatas = [
                {
                    "file_id": c.file_id,
                    "chunk_index": c.chunk_index,
                    "hash": c.hash,
                }
                for c in batch
            ]
            collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    tasks = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        tasks.append(process_batch(batch))

    await asyncio.gather(*tasks)


def delete_repo_index(repo_id: int):
    client = get_chroma_client()
    try:
        client.delete_collection(f"repo_{repo_id}")
    except Exception:
        pass
