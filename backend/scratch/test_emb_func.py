import asyncio
from app.services.indexer import get_embedding
from app.config import get_settings

async def main():
    settings = get_settings()
    print("Embedding model:", settings.EMBEDDING_MODEL)
    res = await get_embedding(["Hello RepoLens AI"])
    print("Result length:", len(res))
    print("Is all zero?", all(x == 0.0 for x in res[0]))
    print("First 10 values:", res[0][:10])

if __name__ == "__main__":
    asyncio.run(main())
