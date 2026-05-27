import os
import re
import shutil
import subprocess
import stat
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from app.models import Repository, File
from app.config import get_settings

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def parse_github_url(url: str):
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace(".git", "")
    parts = path.split("/")
    if len(parts) < 2:
        raise ValueError("Invalid GitHub URL")
    return parts[0], parts[1]

def clone_repository(db: Session, github_url: str, branch: str = None) -> Repository:
    owner, name = parse_github_url(github_url)
    settings = get_settings()
    clone_dir = os.path.join(settings.CLONE_DIR, f"{owner}_{name}")

    repo = Repository(
        github_url=github_url,
        name=name,
        owner=owner,
        default_branch=branch or "main",
        status="cloning",
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir, onerror=remove_readonly)

    try:
        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd += ["--branch", branch]
        cmd += [github_url, clone_dir]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        repo.status = "parsing"
        db.commit()
    except subprocess.CalledProcessError as e:
        repo.status = "error"
        repo.status_message = str(e.stderr or e.stdout)
        db.commit()
        raise

    return repo, clone_dir

def scan_files(repo: Repository, clone_dir: str, db: Session):
    ignore_patterns = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".next", ".idea", ".vscode"}
    language_map = {
        ".py": "python", ".js": "javascript", ".jsx": "jsx", ".ts": "typescript",
        ".tsx": "tsx", ".java": "java", ".go": "go", ".cpp": "cpp", ".c": "c",
        ".h": "c", ".json": "json", ".yaml": "yaml", ".yml": "yaml",
        ".md": "markdown", ".sql": "sql", ".html": "html", ".css": "css",
    }
    lang_counts = {}
    file_dicts = []      # raw dicts for bulk insert
    file_paths = []      # parallel list of absolute paths

    for root, dirs, files in os.walk(clone_dir):
        dirs[:] = [d for d in dirs if d not in ignore_patterns]
        for fname in files:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, clone_dir).replace("\\", "/")
            ext = os.path.splitext(fname)[1].lower()
            language = language_map.get(ext, "")
            if language:
                lang_counts[language] = lang_counts.get(language, 0) + 1
            size = os.path.getsize(fpath)
            file_dicts.append({
                "repository_id": repo.id,
                "path": rel,
                "file_type": ext,
                "language": language,
                "size": size,
                "parsed_status": "pending",
            })
            file_paths.append(fpath)

    # Bulk insert all file records in one statement
    if file_dicts:
        db.bulk_insert_mappings(File, file_dicts)

    repo.language_summary = lang_counts
    db.commit()

    # Fetch back inserted File objects (with IDs) in one query
    inserted_files = (
        db.query(File)
        .filter(File.repository_id == repo.id, File.parsed_status == "pending")
        .all()
    )
    # Match each File object to its absolute path by the relative path
    path_to_abs = {d["path"]: fp for d, fp in zip(file_dicts, file_paths)}
    files_added = [(f, path_to_abs.get(f.path, "")) for f in inserted_files]

    return files_added

def update_repo_status(db: Session, repo_id: int, status: str, message: str = ""):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if repo:
        repo.status = status
        repo.status_message = (message or "").replace("\x00", "")
        db.commit()
