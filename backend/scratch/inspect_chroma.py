import chromadb
from app.config import get_settings

def inspect():
    settings = get_settings()
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    collections = client.list_collections()
    print("Collections found:")
    for col in collections:
        print(f"Name: {col.name}")
        try:
            print(f" - Count: {col.count()}")
            # Try to get one item to check embeddings dimension
            peek = col.peek(limit=1)
            if peek and peek["embeddings"]:
                print(f" - Embedding Dimension: {len(peek['embeddings'][0])}")
            else:
                print(" - No embeddings found in peek")
        except Exception as e:
            print(f" - Error: {e}")

if __name__ == "__main__":
    inspect()
