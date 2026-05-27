import asyncio
from app.database import SessionLocal
from app.services.indexer import index_chunks, get_collection
from app.config import get_settings

async def main():
    db = SessionLocal()
    repo_id = 5
    settings = get_settings()
    
    # Temporarily override settings
    settings.EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-1b-v2"
    
    print("Deleting old ChromaDB collection...")
    try:
        col = get_collection(repo_id)
        client = col._client
        try:
            client.delete_collection(f"repo_{repo_id}")
        except Exception as e:
            print("Delete collection warning:", e)
    except Exception as e:
        print("Error clearing collection:", e)
        
    print("Re-indexing chunks with llama-nemotron-embed-1b-v2...")
    await index_chunks(repo_id, db)
    
    col = get_collection(repo_id)
    print("New Chroma count:", col.count())
    if col.count() > 0:
        emb = col.get(include=['embeddings'], limit=1)['embeddings'][0]
        print("First 10 values of new embedding:", emb[:10])
        print("Is all zero?", all(x == 0.0 for x in emb))

if __name__ == "__main__":
    asyncio.run(main())
