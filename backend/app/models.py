from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    github_url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    default_branch = Column(String, default="main")
    language_summary = Column(JSON, default=dict)
    status = Column(String, default="pending")  # pending, cloning, parsing, indexing, ready, error
    status_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = relationship("File", back_populates="repository", cascade="all, delete-orphan")
    diagrams = relationship("Diagram", back_populates="repository", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="repository", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    path = Column(String, nullable=False)
    file_type = Column(String, default="")
    language = Column(String, default="")
    hash = Column(String, default="")
    size = Column(Integer, default=0)
    parsed_status = Column(String, default="pending")
    content_preview = Column(Text, default="")

    repository = relationship("Repository", back_populates="files")
    symbols = relationship("Symbol", back_populates="file", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="file", cascade="all, delete-orphan")

class Symbol(Base):
    __tablename__ = "symbols"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    name = Column(String, nullable=False)
    symbol_type = Column(String, nullable=False)  # function, class, variable, import, route
    start_line = Column(Integer, default=0)
    end_line = Column(Integer, default=0)
    visibility = Column(String, default="")
    extra = Column(JSON, default=dict)

    file = relationship("File", back_populates="symbols")

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    embedding_id = Column(String, default="")
    hash = Column(String, default="")

    file = relationship("File", back_populates="chunks")

class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, default="")
    retrieved_chunks = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship("Repository", back_populates="query_logs")

class Diagram(Base):
    __tablename__ = "diagrams"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    type = Column(String, nullable=False)  # dependency, flow, architecture
    payload = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship("Repository", back_populates="diagrams")
