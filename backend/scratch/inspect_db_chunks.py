import asyncio
import httpx
from app.database import SessionLocal
from app.models import Chunk, File
from app.config import get_settings

async def main():
    db = SessionLocal()
    settings = get_settings()
    repo_id = 5
    chunks = db.query(Chunk).join(File).filter(File.repository_id == repo_id).all()
    print("Total chunks in DB:", len(chunks))
    
    # Try embedding the first chunk
    if chunks:
        c = chunks[0]
        print(f"Chunk 0 ID: {c.id}, length: {len(c.content)}")
        print("Chunk 0 Content sample:")
        print(repr(c.content[:200]))
        
        # Test request with this chunk content
        async with httpx.AsyncClient() as client:
            payload = {
                "input": [c.content],
                "model": settings.EMBEDDING_MODEL,
                "input_type": "passage"
            }
            resp = await client.post(
                f"{settings.OPENAI_BASE_URL}/embeddings",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json=payload,
                timeout=20.0,
            )
            print(f"Status: {resp.status_code}")
            if resp.status_code != 200:
                print("Failed! Response:", resp.text)
            else:
                print("Success embedding Chunk 0!")

if __name__ == "__main__":
    asyncio.run(main())
