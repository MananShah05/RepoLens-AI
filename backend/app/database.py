from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.models import Base

settings = get_settings()

_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = dict(
    pool_pre_ping=True,
)

if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Remote PostgreSQL (Neon) — tune pool for network latency
    _engine_kwargs.update(
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=300,  # Recycle connections every 5 min (Neon idle-disconnect)
        executemany_mode="values_only",  # Fast psycopg2 multi-row inserts
    )

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
