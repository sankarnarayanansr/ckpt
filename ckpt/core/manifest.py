import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class Manifest:
    id: str
    message: str
    created_at: str           # ISO 8601
    entries: List[Dict]       # [{path, hash, size}]
    tags: List[str] = field(default_factory=list)
    tool_meta: Optional[Dict] = None

    @property
    def short_id(self) -> str:
        return self.id[:7]

    @property
    def created_dt(self) -> datetime:
        return datetime.fromisoformat(self.created_at)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> "Manifest":
        return cls(**d)

def delete(m: Manifest, root: str = "."):
    mdir = _manifest_dir(root)
    path = mdir / f"{m.id}.json"
    if path.exists():
        path.unlink()
    # Update HEAD if we deleted the current one
    head = Path(root) / ".ckpt" / "HEAD"
    if head.exists() and head.read_text().strip() == m.id:
        remaining = load_all(root=root)
        head.write_text(remaining[0].id if remaining else "")


def create(oid: str, message: str, entries: List[Dict], stats: Dict) -> Manifest:
    return Manifest(
        id=oid,
        message=message,
        created_at=datetime.now(timezone.utc).isoformat(),
        entries=entries,
    )


def _manifest_dir(root: str) -> Path:
    return Path(root) / ".ckpt" / "manifests"


def save(m: Manifest, root: str = ".", overwrite: bool = False):
    mdir = _manifest_dir(root)
    mdir.mkdir(parents=True, exist_ok=True)
    path = mdir / f"{m.id}.json"
    if path.exists() and not overwrite:
        return
    path.write_text(json.dumps(m.to_dict(), indent=2))

    # Update HEAD
    head = Path(root) / ".ckpt" / "HEAD"
    head.write_text(m.id)


def load_by_id(checkpoint_id: str, root: str = ".") -> Optional[Manifest]:
    mdir = _manifest_dir(root)
    # Support short IDs — find any manifest whose filename starts with checkpoint_id
    for p in mdir.glob("*.json"):
        if p.stem.startswith(checkpoint_id):
            data = json.loads(p.read_text())
            return Manifest.from_dict(data)
    return None


def load_all(root: str = ".") -> List[Manifest]:
    mdir = _manifest_dir(root)
    if not mdir.exists():
        return []
    manifests = []
    for p in sorted(mdir.glob("*.json"), reverse=True):
        try:
            data = json.loads(p.read_text())
            manifests.append(Manifest.from_dict(data))
        except Exception:
            continue
    # Sort by created_at descending
    manifests.sort(key=lambda m: m.created_at, reverse=True)
    return manifests
