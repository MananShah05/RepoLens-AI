from typing import List, Dict
from sqlalchemy.orm import Session, joinedload
from app.models import Repository, File, Symbol, Diagram
import os

def build_dependency_graph(repo_id: int, db: Session) -> str:
    files = db.query(File).filter(File.repository_id == repo_id).all()
    symbols = (
        db.query(Symbol)
        .options(joinedload(Symbol.file))
        .join(File)
        .filter(File.repository_id == repo_id, Symbol.symbol_type == "import")
        .all()
    )

    nodes = set()
    edges = []

    for f in files:
        if f.language in ("javascript", "typescript", "python", "java", "go"):
            nodes.add(f.path)

    # Simple heuristic: if import mentions another file in repo
    file_names = {os.path.splitext(f.path)[0].replace("\\", "/"): f.path for f in files}

    for sym in symbols:
        src = sym.file.path
        imp_text = sym.name.lower()
        for stem, fpath in file_names.items():
            if stem == os.path.splitext(src)[0].replace("\\", "/"):
                continue
            # naive match
            parts = stem.split("/")
            name = parts[-1]
            if name and name.lower() in imp_text:
                edges.append((src, fpath))

    lines = ["graph TD"]
    node_ids = {}
    for i, n in enumerate(sorted(nodes)):
        node_ids[n] = f"N{i}"
        safe_label = n.replace('"', "'")
        lines.append(f'    {node_ids[n]}["{safe_label}"]')

    seen_edges = set()
    for a, b in edges:
        if a in node_ids and b in node_ids:
            key = (node_ids[a], node_ids[b])
            if key not in seen_edges:
                seen_edges.add(key)
                lines.append(f"    {node_ids[a]} --> {node_ids[b]}")

    return "\n".join(lines)

def build_file_tree(repo_id: int, db: Session) -> List[Dict]:
    files = db.query(File).filter(File.repository_id == repo_id).all()
    tree = {}
    for f in files:
        parts = f.path.split("/")
        curr = tree
        for part in parts[:-1]:
            if part not in curr:
                curr[part] = {"_type": "folder", "children": {}}
            curr = curr[part]["children"]
        curr[parts[-1]] = {"_type": "file", "id": f.id, "language": f.language}

    def convert(node):
        result = []
        for name, data in sorted(node.items()):
            if name == "_type":
                continue
            if data.get("_type") == "folder":
                result.append({
                    "name": name,
                    "type": "folder",
                    "children": convert(data.get("children", {})),
                })
            else:
                result.append({
                    "name": name,
                    "type": "file",
                    "id": data.get("id"),
                    "language": data.get("language"),
                })
        return result

    return convert(tree)

def save_or_update_diagram(repo_id: int, dtype: str, payload: str, db: Session):
    diag = db.query(Diagram).filter(Diagram.repository_id == repo_id, Diagram.type == dtype).first()
    if diag:
        diag.payload = payload
        diag.version += 1
    else:
        diag = Diagram(repository_id=repo_id, type=dtype, payload=payload)
        db.add(diag)
    db.commit()
    return diag
