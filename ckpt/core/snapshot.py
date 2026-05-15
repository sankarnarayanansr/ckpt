import hashlib
import os
from pathlib import Path
from typing import List, Dict
from ckpt.core.ignore import IgnoreRules


def take(root: str = ".") -> List[Dict]:
    """
    Walk the project directory and hash every file.
    Returns a list of dicts: {path, hash, size}
    Skips .ckpt/ directory and files matching .ckptignore rules.
    """
    root_path = Path(root).resolve()
    rules = IgnoreRules.load(root_path)
    entries = []

    for abs_path in sorted(root_path.rglob("*")):
        if not abs_path.is_file():
            continue

        rel = abs_path.relative_to(root_path)
        rel_str = str(rel)

        # Always skip the store itself
        if rel_str.startswith(".ckpt"):
            continue

        if rules.match(rel_str):
            continue

        entries.append({
            "path": rel_str,
            "hash": sha256_stream(abs_path),
            "size": abs_path.stat().st_size,
        })

    return entries


def sha256_stream(path: Path) -> str:
    """Hash a file in 8MB chunks — safe for large binaries."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
