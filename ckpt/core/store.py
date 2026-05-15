import json
import shutil
import tarfile
import time
from pathlib import Path
from typing import List, Dict, Tuple

from ckpt.core.manifest import Manifest


def _store_root(root: str, store_path: str = None) -> Path:
    if store_path:
        return Path(store_path)
    return Path(root) / ".ckpt" / "objects"


def write(entries: List[Dict], root: str = ".", store_path: str = None) -> Tuple[str, Dict]:
    """
    Write file objects to the content-addressed store.
    Files with the same hash are stored only once (dedup).
    Returns (checkpoint_id, stats_dict).
    """
    store_dir = _store_root(root, store_path)
    store_dir.mkdir(parents=True, exist_ok=True)

    root_path = Path(root).resolve()
    t0 = time.time()

    total_size = 0
    stored_size = 0
    new_objects = 0

    for entry in entries:
        h = entry["hash"]
        size = entry["size"]
        total_size += size

        # Content-addressed path: objects/a4/f2c8d1a2b3...
        obj_path = store_dir / h[:2] / h[2:]
        if obj_path.exists():
            continue  # already stored — dedup hit

        obj_path.parent.mkdir(parents=True, exist_ok=True)
        src = root_path / entry["path"]
        _copy_chunked(src, obj_path)
        stored_size += size
        new_objects += 1

    elapsed = time.time() - t0

    # Derive a short ID from the combined hash of all entry hashes
    import hashlib
    combined = hashlib.sha256(
        "".join(e["hash"] for e in entries).encode()
    ).hexdigest()[:7]

    stats = {
        "id": combined,
        "file_count": len(entries),
        "total_bytes": total_size,
        "stored_bytes": stored_size,
        "new_objects": new_objects,
        "elapsed": elapsed,
    }
    return combined, stats


def restore(m: Manifest, root: str = "."):
    """Restore all files from a checkpoint manifest."""
    store_dir = _store_root(root)
    root_path = Path(root).resolve()

    for entry in m.entries:
        h = entry["hash"]
        obj_path = store_dir / h[:2] / h[2:]
        dest = root_path / entry["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(obj_path, dest)


def export(m: Manifest, output_path: str, root: str = ".") -> int:
    """Export a checkpoint as a tar.gz archive. Returns file size in bytes."""
    store_dir = _store_root(root)

    with tarfile.open(output_path, "w:gz") as tar:
        for entry in m.entries:
            h = entry["hash"]
            obj_path = store_dir / h[:2] / h[2:]
            tar.add(obj_path, arcname=entry["path"])

    return Path(output_path).stat().st_size


def _copy_chunked(src: Path, dest: Path, chunk: int = 8 << 20):
    """Copy a file in chunks — handles 2GB+ files safely."""
    with open(src, "rb") as f_in, open(dest, "wb") as f_out:
        for block in iter(lambda: f_in.read(chunk), b""):
            f_out.write(block)
