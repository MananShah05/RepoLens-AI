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
    print("Total chunks:", len(chunks))
    
    batch = chunks[:32]
    texts = [c.content for c in batch]
    
    async with httpx.AsyncClient() as client:
        payload = {
            "input": texts,
            "model": settings.EMBEDDING_MODEL,
            "input_type": "passage"
        }
        resp = await client.post(
            f"{settings.OPENAI_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json=payload,
            timeout=20.0,
        )
        print(f"Batch status code: {resp.status_code}")
        if resp.status_code != 200:
            print("Failed! Response details:")
            print(resp.text)
        else:
            print("Successfully embedded batch of size 32!")

if __name__ == "__main__":
    asyncio.run(main())
