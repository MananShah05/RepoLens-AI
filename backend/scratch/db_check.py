from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.models import Repository, File, Symbol, Chunk
from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("--- REPOSITORIES ---")
repos = db.query(Repository).all()
for r in repos:
    print(f"ID: {r.id} | Name: {r.name} | Status: {r.status} | Status Msg: {r.status_message}")
    # Count files
    file_count = db.query(File).filter(File.repository_id == r.id).count()
    parsed_count = db.query(File).filter(File.repository_id == r.id, File.parsed_status == "parsed").count()
    skipped_count = db.query(File).filter(File.repository_id == r.id, File.parsed_status == "skipped").count()
    error_count = db.query(File).filter(File.repository_id == r.id, File.parsed_status == "error").count()
    pending_count = db.query(File).filter(File.repository_id == r.id, File.parsed_status == "pending").count()
    
    print(f"  Total Files: {file_count} (Parsed: {parsed_count}, Skipped: {skipped_count}, Error: {error_count}, Pending: {pending_count})")
    
    # Count chunks
    chunk_count = db.query(Chunk).join(File).filter(File.repository_id == r.id).count()
    symbol_count = db.query(Symbol).join(File).filter(File.repository_id == r.id).count()
    print(f"  Chunks: {chunk_count} | Symbols: {symbol_count}")
db.close()
