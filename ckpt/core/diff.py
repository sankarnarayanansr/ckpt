from typing import List, Dict
from ckpt.core.manifest import Manifest


def compare(m_a: Manifest, m_b: Manifest) -> List[Dict]:
    """
    Compare two manifests and return a list of changes.
    Each change: {status, path, size_a, size_b, hash_a, hash_b}
    status: 'M' modified, 'A' added, 'D' deleted
    """
    map_a = {e["path"]: e for e in m_a.entries}
    map_b = {e["path"]: e for e in m_b.entries}

    all_paths = sorted(set(map_a) | set(map_b))
    changes = []

    for path in all_paths:
        in_a = path in map_a
        in_b = path in map_b

        if in_a and in_b:
            if map_a[path]["hash"] != map_b[path]["hash"]:
                changes.append({
                    "status": "M",
                    "path": path,
                    "size_a": map_a[path]["size"],
                    "size_b": map_b[path]["size"],
                    "hash_a": map_a[path]["hash"],
                    "hash_b": map_b[path]["hash"],
                })
        elif in_b and not in_a:
            changes.append({
                "status": "A",
                "path": path,
                "size_a": 0,
                "size_b": map_b[path]["size"],
                "hash_a": None,
                "hash_b": map_b[path]["hash"],
            })
        else:
            changes.append({
                "status": "D",
                "path": path,
                "size_a": map_a[path]["size"],
                "size_b": 0,
                "hash_a": map_a[path]["hash"],
                "hash_b": None,
            })

    return changes
