from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./repolens.db"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHAT_MODEL: str = "gpt-4o-mini"
    CLONE_DIR: str = "./repos"
    MAX_CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 200

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
