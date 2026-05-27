import os
import time
import hashlib
from typing import List, Tuple
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjs
import tree_sitter_typescript as tsts
import tree_sitter_java as tsjava
import tree_sitter_go as tsgo

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

QUERIES["jsx"] = QUERIES["javascript"]
QUERIES["tsx"] = QUERIES["typescript"]

# Original Implementation
def file_hash_orig(filepath: str) -> str:
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]

def detect_imports_orig(content: str, language: str) -> List[str]:
    imports = []
    if language in ("python",):
        for line in content.splitlines():
            if line.strip().startswith(("import ", "from ")):
                imports.append(line.strip())
    elif language in ("javascript", "typescript", "jsx", "tsx"):
        for line in content.splitlines():
            if line.strip().startswith(("import ", "require(")):
                imports.append(line.strip())
    elif language == "java":
        for line in content.splitlines():
            if line.strip().startswith("import "):
                imports.append(line.strip())
    elif language == "go":
        for line in content.splitlines():
            if line.strip().startswith("import "):
                imports.append(line.strip())
    return imports

def parse_single_file_data_orig(filepath: str, language: str, max_chunk_size: int, chunk_overlap: int) -> dict:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception:
        return {
            "status": "error",
            "hash": "",
            "content_preview": "",
            "symbols": [],
            "chunks": []
        }

    if len(content) > 500_000:
        return {
            "status": "skipped",
            "hash": "",
            "content_preview": content[:2000],
            "symbols": [],
            "chunks": []
        }

    f_hash = file_hash_orig(filepath)
    content_preview = content[:2000]

    symbols = []
    if language in LANGUAGE_MAP:
        try:
            parser = Parser(LANGUAGE_MAP[language])
            tree = parser.parse(bytes(content, "utf8"))
            query_str = QUERIES.get(language, "")
            if query_str:
                query = LANGUAGE_MAP[language].query(query_str)
                captures = query.captures(tree.root_node)
                for node, capture_name in captures:
                    if capture_name == "name":
                        symbol_name = content[node.start_byte:node.end_byte]
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
            pass

    for imp in detect_imports_orig(content, language):
        symbols.append({
            "name": imp[:120],
            "symbol_type": "import",
            "start_line": 0,
            "end_line": 0,
        })

    chunks = []
    overlap_lines = max(5, chunk_overlap // 80)

    if language in LANGUAGE_MAP and symbols:
        seen = set()
        for sym in symbols:
            if sym["symbol_type"] == "import":
                continue
            key = (sym["start_line"], sym["end_line"])
            if key in seen:
                continue
            seen.add(key)
            lines = content.splitlines()
            start = max(0, sym["start_line"] - 1)
            end = min(len(lines), sym["end_line"] + 5)
            chunk_text = "\n".join(lines[start:end])
            if chunk_text.strip():
                chunks.append({
                    "content": chunk_text,
                    "chunk_index": len(chunks),
                    "hash": hashlib.sha256(chunk_text.encode()).hexdigest()[:16],
                })

    if not chunks or len(content) > max_chunk_size * 2:
        lines = content.splitlines()
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
                    "hash": hashlib.sha256(chunk_text.encode()).hexdigest()[:16],
                })
                current = current[-overlap_lines:]
                current_len = sum(len(l) + 1 for l in current)
        if current:
            chunk_text = "\n".join(current)
            chunks.append({
                "content": chunk_text,
                "chunk_index": len(chunks),
                "hash": hashlib.sha256(chunk_text.encode()).hexdigest()[:16],
            })

    return {
        "status": "parsed",
        "hash": f_hash,
        "content_preview": content_preview,
        "symbols": symbols,
        "chunks": chunks
    }

# Optimized Implementation
COMPILED_QUERIES = {}
for lang_name, lang_obj in LANGUAGE_MAP.items():
    q_str = QUERIES.get(lang_name)
    if q_str:
        COMPILED_QUERIES[lang_name] = lang_obj.query(q_str)

def detect_imports_opt(lines: List[str], language: str) -> List[str]:
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

def parse_single_file_data_opt(filepath: str, language: str, max_chunk_size: int, chunk_overlap: int) -> dict:
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
        content = content_bytes[:2000].decode("utf-8", errors="ignore")
        return {
            "status": "skipped",
            "hash": "",
            "content_preview": content,
            "symbols": [],
            "chunks": []
        }

    f_hash = hashlib.sha256(content_bytes).hexdigest()[:16]
    content = content_bytes.decode("utf-8", errors="ignore")
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
                for node, capture_name in captures:
                    if capture_name == "name":
                        symbol_bytes = content_bytes[node.start_byte:node.end_byte]
                        symbol_name = symbol_bytes.decode("utf-8", errors="ignore")
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
            pass

    # Imports as symbols
    for imp in detect_imports_opt(lines, language):
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

# Main benchmark runner
if __name__ == "__main__":
    test_dir = r"c:\Users\MS\Documents\Code\RepoLens AI\backend\repos\MananShah05_transcend-frames"
    ext_map = {
        ".js": "javascript",
        ".jsx": "jsx",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".py": "python",
    }
    
    files_to_test = []
    for root, _, files in os.walk(test_dir):
        if any(ignore in root for ignore in [".git", "node_modules", ".next"]):
            continue
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext in ext_map:
                files_to_test.append((os.path.join(root, f), ext_map[ext]))

    print(f"Found {len(files_to_test)} files to benchmark.")
    
    # Warm up tree-sitter
    if files_to_test:
        parse_single_file_data_orig(files_to_test[0][0], files_to_test[0][1], 1500, 200)
        parse_single_file_data_opt(files_to_test[0][0], files_to_test[0][1], 1500, 200)

    # Benchmark original
    t0 = time.perf_counter()
    for fp, lang in files_to_test:
        parse_single_file_data_orig(fp, lang, 1500, 200)
    t_orig = time.perf_counter() - t0
    print(f"Original parser took: {t_orig:.4f}s")

    # Benchmark optimized
    t0 = time.perf_counter()
    for fp, lang in files_to_test:
        parse_single_file_data_opt(fp, lang, 1500, 200)
    t_opt = time.perf_counter() - t0
    print(f"Optimized parser took: {t_opt:.4f}s")
    
    # Calculate speedup
    speedup = t_orig / t_opt if t_opt > 0 else 0
    print(f"Speedup: {speedup:.2f}x")

    # Verify correctness
    mismatches = 0
    for fp, lang in files_to_test:
        res_orig = parse_single_file_data_orig(fp, lang, 1500, 200)
        res_opt = parse_single_file_data_opt(fp, lang, 1500, 200)
        
        # Verify hashes match
        if res_orig["hash"] != res_opt["hash"]:
            print(f"Hash mismatch for {fp}")
            mismatches += 1
            
        # Verify number of symbols match
        if len(res_orig["symbols"]) != len(res_opt["symbols"]):
            print(f"Symbols len mismatch for {fp}: orig={len(res_orig['symbols'])}, opt={len(res_opt['symbols'])}")
            mismatches += 1
            
        # Verify number of chunks match
        if len(res_orig["chunks"]) != len(res_opt["chunks"]):
            print(f"Chunks len mismatch for {fp}: orig={len(res_orig['chunks'])}, opt={len(res_opt['chunks'])}")
            mismatches += 1
            
    print(f"Correctness verification complete: {mismatches} mismatches found.")
