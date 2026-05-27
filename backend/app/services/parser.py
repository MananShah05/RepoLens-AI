import os
import hashlib
import logging
from typing import List, Tuple
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tsts
import tree_sitter_java as tsjava
import tree_sitter_go as tsgo

from app.config import get_settings
from app.models import File, Symbol, Chunk
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    "python": Language(tspython.language()),
    "javascript": Language(tsjs.language()),
    "jsx": Language(tsjs.language()),
    "typescript": Language(tsts.language_typescript()),
    "tsx": Language(tsts.language_tsx()),
    "java": Language(tsjava.language()),
    "go": Language(tsgo.language()),
}

QUERIES = {
    "python": """
        (function_definition name: (identifier) @name) @symbol
        (class_definition name: (identifier) @name) @symbol
    """,
    "javascript": """
        (function_declaration name: (identifier) @name) @symbol
        (class_declaration name: (identifier) @name) @symbol
        (method_definition name: (property_identifier) @name) @symbol
        (arrow_function) @symbol
    """,
    "typescript": """
        (function_declaration name: (identifier) @name) @symbol
        (class_declaration name: (type_identifier) @name) @symbol
        (method_definition name: (property_identifier) @name) @symbol
        (interface_declaration name: (type_identifier) @name) @symbol
        (type_alias_declaration name: (type_identifier) @name) @symbol
        (enum_declaration name: (identifier) @name) @symbol
    """,
    "java": """
        (method_declaration name: (identifier) @name) @symbol
        (class_declaration name: (identifier) @name) @symbol
    """,
    "go": """
        (function_declaration name: (identifier) @name) @symbol
        (method_declaration name: (field_identifier) @name) @symbol
        (type_declaration (type_spec name: (type_identifier) @name)) @symbol
    """,
}

# Use same queries for jsx/tsx as their base languages
QUERIES["jsx"] = QUERIES["javascript"]
QUERIES["tsx"] = QUERIES["typescript"]

# Precompile queries to avoid dynamic overhead for each file
COMPILED_QUERIES = {}
for lang_name, lang_obj in LANGUAGE_MAP.items():
    q_str = QUERIES.get(lang_name)
    if q_str:
        COMPILED_QUERIES[lang_name] = lang_obj.query(q_str)


def file_hash(filepath: str) -> str:
    # Deprecated: use inline hashing of loaded bytes to avoid double file reads.
    # Kept for backward compatibility if called elsewhere.
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def detect_imports(lines: List[str], language: str) -> List[str]:
    imports = []
    if language in ("python",):
        for line in lines:
            if line.strip().startswith(("import ", "from ")):
                imports.append(line.strip())
    elif language in ("javascript", "typescript", "jsx", "tsx"):
        for line in lines:
            if line.strip().startswith(("import ", "require(")):
                imports.append(line.strip())
    elif language == "java":
        for line in lines:
            if line.strip().startswith("import "):
                imports.append(line.strip())
    elif language == "go":
        for line in lines:
            if line.strip().startswith("import "):
                imports.append(line.strip())
    return imports


def parse_single_file_data(filepath: str, language: str, max_chunk_size: int, chunk_overlap: int) -> dict:
    try:
        with open(filepath, "rb") as f:
            content_bytes = f.read()
    except Exception:
        return {
            "status": "error",
            "hash": "",
            "content_preview": "",
            "symbols": [],
            "chunks": []
        }

    # Skip very large files (>500KB)
    if len(content_bytes) > 500_000:
        content = content_bytes[:2000].decode("utf-8", errors="ignore").replace("\x00", "")
        return {
            "status": "skipped",
            "hash": "",
            "content_preview": content,
            "symbols": [],
            "chunks": []
        }

    f_hash = hashlib.sha256(content_bytes).hexdigest()[:16]
    content = content_bytes.decode("utf-8", errors="ignore").replace("\x00", "")
    content_preview = content[:2000]
    lines = content.splitlines()

    symbols = []
    # Symbol extraction
    if language in LANGUAGE_MAP:
        try:
            parser = Parser(LANGUAGE_MAP[language])
            tree = parser.parse(content_bytes)
            query = COMPILED_QUERIES.get(language)
            if query:
                captures = query.captures(tree.root_node)
                # tree-sitter returns list of (node, capture_name) tuples
                for node, capture_name in captures:
                    if capture_name == "name":
                        # Correctly slice the raw byte offsets and decode
                        symbol_bytes = content_bytes[node.start_byte:node.end_byte]
                        symbol_name = symbol_bytes.decode("utf-8", errors="ignore").replace("\x00", "")
                        parent = node.parent
                        symbol_type = "function"
                        if parent:
                            if "class" in parent.type:
                                symbol_type = "class"
                            elif "interface" in parent.type:
                                symbol_type = "interface"
                            elif "method" in parent.type:
                                symbol_type = "method"
                        symbols.append({
                            "name": symbol_name,
                            "symbol_type": symbol_type,
                            "start_line": node.start_point[0] + 1,
                            "end_line": node.end_point[0] + 1,
                        })
        except Exception as e:
            logger.warning(f"Symbol extraction failed for {filepath}: {e}")

    # Imports as symbols
    for imp in detect_imports(lines, language):
        symbols.append({
            "name": imp[:120],
            "symbol_type": "import",
            "start_line": 0,
            "end_line": 0,
        })

    # Chunking
    chunks = []
    overlap_lines = max(5, chunk_overlap // 80)  # Convert char overlap to approx lines

    if language in LANGUAGE_MAP and symbols:
        # Chunk by symbols when possible
        seen = set()
        for sym in symbols:
            if sym["symbol_type"] == "import":
                continue
            key = (sym["start_line"], sym["end_line"])
            if key in seen:
                continue
            seen.add(key)
            start = max(0, sym["start_line"] - 1)
            end = min(len(lines), sym["end_line"] + 5)
            chunk_text = "\n".join(lines[start:end])
            if chunk_text.strip():
                chunks.append({
                    "content": chunk_text,
                    "chunk_index": len(chunks),
                    "hash": hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()[:16],
                })

    # Fallback / large file line-based chunking
    if not chunks or len(content) > max_chunk_size * 2:
        current = []
        current_len = 0
        for line in lines:
            current.append(line)
            current_len += len(line) + 1
            if current_len >= max_chunk_size:
                chunk_text = "\n".join(current)
                chunks.append({
                    "content": chunk_text,
                    "chunk_index": len(chunks),
                    "hash": hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()[:16],
                })
                # overlap: keep last few lines
                current = current[-overlap_lines:]
                current_len = sum(len(l) + 1 for l in current)
        if current:
            chunk_text = "\n".join(current)
            chunks.append({
                "content": chunk_text,
                "chunk_index": len(chunks),
                "hash": hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()[:16],
            })


    return {
        "status": "parsed",
        "hash": f_hash,
        "content_preview": content_preview,
        "symbols": symbols,
        "chunks": chunks
    }


def parse_file(file_obj: File, filepath: str, db: Session) -> Tuple[List[Symbol], List[Chunk]]:
    settings = get_settings()
    res = parse_single_file_data(
        filepath,
        file_obj.language,
        settings.MAX_CHUNK_SIZE,
        settings.CHUNK_OVERLAP
    )

    file_obj.parsed_status = res["status"]
    file_obj.hash = res["hash"]
    file_obj.content_preview = res["content_preview"]

    symbols = []
    chunks = []

    if res["status"] == "parsed":
        for sym_data in res["symbols"]:
            sym = Symbol(
                file_id=file_obj.id,
                name=sym_data["name"],
                symbol_type=sym_data["symbol_type"],
                start_line=sym_data["start_line"],
                end_line=sym_data["end_line"],
            )
            db.add(sym)
            symbols.append(sym)

        for chunk_data in res["chunks"]:
            chunk = Chunk(
                file_id=file_obj.id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                hash=chunk_data["hash"],
            )
            db.add(chunk)
            chunks.append(chunk)

    db.commit()  # Caller may also batch — but keep commit here for standalone usage
    return symbols, chunks

