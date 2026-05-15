# ckpt — Complete Codebase

---

# ckpt/__main__.py

```python
from ckpt.cli import cli

if __name__ == "__main__":
    cli()
```

---

# ckpt/cli.py

```python
import click
from ckpt.commands import save, restore, list_cmd, diff, tag, export

@click.group()
@click.version_option(version="1.0.0", prog_name="ckpt")
def cli():
    """ckpt — dead-simple project checkpoint tool for EDA and beyond."""
    pass

cli.add_command(save.cmd,        "save")
cli.add_command(restore.cmd,     "restore")
cli.add_command(list_cmd.cmd,    "list")
cli.add_command(diff.cmd,        "diff")
cli.add_command(tag.cmd,         "tag")
cli.add_command(export.cmd,      "export")
```

---

# ckpt/commands/__init__.py



---

# ckpt/commands/save.py

```python
import click
from ckpt.core import snapshot, store, manifest
from ckpt.output import printer


@click.command()
@click.argument("message")
@click.option("--store-path", default=None, help="Custom store path (default: .ckpt/)")
@click.option("--root", default=".", help="Project root directory")
def cmd(message, store_path, root):
    """Save a checkpoint of the current project state.

    Example: ckpt save "after timing closure attempt 3"
    """
    with printer.spinner("Scanning project files..."):
        snap = snapshot.take(root=root)

    with printer.spinner("Writing objects to store..."):
        oid, stats = store.write(snap, root=root, store_path=store_path)

    m = manifest.create(oid, message, snap, stats)
    manifest.save(m, root=root)
    printer.saved(m, stats)
```

---

# ckpt/commands/restore.py

```python
import click
from ckpt.core import manifest, store
from ckpt.output import printer


@click.command()
@click.argument("checkpoint_id")
@click.option("--root", default=".", help="Project root directory")
@click.option("--dry-run", is_flag=True, help="Show what would be restored without doing it")
def cmd(checkpoint_id, root, dry_run):
    """Restore project to a previous checkpoint.

    Example: ckpt restore 9e1b3ac
    """
    m = manifest.load_by_id(checkpoint_id, root=root)
    if m is None:
        printer.error(f"Checkpoint '{checkpoint_id}' not found.")
        raise click.Abort()

    if dry_run:
        printer.dry_run(m)
        return

    with printer.spinner(f"Restoring {m.short_id}..."):
        store.restore(m, root=root)

    printer.restored(m)
```

---

# ckpt/commands/list_cmd.py

```python
fimport click
from ckpt.core import manifest
from ckpt.output import printer


@click.command()
@click.option("--root", default=".", help="Project root directory")
@click.option("--limit", default=20, help="Number of checkpoints to show")
@click.option("--tag", "filter_tag", default=None, help="Filter by tag")
def cmd(root, limit, filter_tag):
    """List all checkpoints.

    Example: ckpt list
             ckpt list --tag golden
    """
    manifests = manifest.load_all(root=root)

    if filter_tag:
        manifests = [m for m in manifests if filter_tag in m.tags]

    manifests = manifests[:limit]

    if not manifests:
        printer.info("No checkpoints found. Run: ckpt save \"your message\"")
        return

    printer.list_checkpoints(manifests)
```

---

# ckpt/commands/diff.py

```python
import click
from ckpt.core import manifest, diff as core_diff
from ckpt.output import printer


@click.command()
@click.argument("id_a")
@click.argument("id_b")
@click.option("--root", default=".", help="Project root directory")
def cmd(id_a, id_b, root):
    """Show what changed between two checkpoints.

    Example: ckpt diff 9e1b3ac a4f2c8d
    """
    m_a = manifest.load_by_id(id_a, root=root)
    m_b = manifest.load_by_id(id_b, root=root)

    if m_a is None:
        printer.error(f"Checkpoint '{id_a}' not found.")
        raise click.Abort()
    if m_b is None:
        printer.error(f"Checkpoint '{id_b}' not found.")
        raise click.Abort()

    changes = core_diff.compare(m_a, m_b)
    printer.diff(m_a, m_b, changes)
```

---

# ckpt/commands/tag.py

```python
import click
from ckpt.core import manifest
from ckpt.output import printer


@click.command()
@click.argument("checkpoint_id")
@click.argument("label")
@click.option("--root", default=".", help="Project root directory")
@click.option("--remove", is_flag=True, help="Remove this tag instead of adding it")
def cmd(checkpoint_id, label, root, remove):
    """Tag a checkpoint with a label.

    Example: ckpt tag 9e1b3ac golden
             ckpt tag 9e1b3ac golden --remove
    """
    m = manifest.load_by_id(checkpoint_id, root=root)
    if m is None:
        printer.error(f"Checkpoint '{checkpoint_id}' not found.")
        raise click.Abort()

    if remove:
        if label in m.tags:
            m.tags.remove(label)
        printer.info(f"Removed tag '{label}' from {m.short_id}")
    else:
        if label not in m.tags:
            m.tags.append(label)
        printer.info(f"Tagged {m.short_id} as '{label}'")

    manifest.save(m, root=root, overwrite=True)
```

---

# ckpt/commands/export.py

```python
import click
from ckpt.core import manifest, store
from ckpt.output import printer


@click.command()
@click.argument("checkpoint_id")
@click.argument("output_path")
@click.option("--root", default=".", help="Project root directory")
def cmd(checkpoint_id, output_path, root):
    """Export a checkpoint as a portable tar.gz archive.

    Example: ckpt export 9e1b3ac golden-state.tar.gz
    """
    m = manifest.load_by_id(checkpoint_id, root=root)
    if m is None:
        printer.error(f"Checkpoint '{checkpoint_id}' not found.")
        raise click.Abort()

    with printer.spinner(f"Exporting {m.short_id}..."):
        size = store.export(m, output_path, root=root)

    printer.exported(m, output_path, size)
```

---

# ckpt/core/__init__.py

```python

```

---

# ckpt/core/snapshot.py

```python
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
```

---

# ckpt/core/store.py

```python
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
```

---

# ckpt/core/manifest.py

```python
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
```

---

# ckpt/core/ignore.py

```python
import fnmatch
from pathlib import Path
from typing import List


DEFAULT_IGNORE_PATTERNS = [
    # Vivado generated
    "*.cache/*",
    "*.ip_user_files/*",
    "*.sim/*",
    "*.hbs",
    "*.log",
    "*.jou",
    "*.str",
    "vivado_*.backup.jou",
    "vivado_*.backup.log",
    # Quartus generated
    "db/*",
    "incremental_db/*",
    "*.rpt",
    "*.pin",
    "*.smsg",
    "*.summary",
    "*.done",
    # ModelSim / Questa
    "work/*",
    "transcript",
    "vsim.wlf",
    # General
    "__pycache__/*",
    "*.pyc",
    ".DS_Store",
    "Thumbs.db",
]


class IgnoreRules:
    def __init__(self, patterns: List[str]):
        self.patterns = patterns

    @classmethod
    def load(cls, root: Path) -> "IgnoreRules":
        patterns = list(DEFAULT_IGNORE_PATTERNS)
        ignore_file = root / ".ckptignore"
        if ignore_file.exists():
            for line in ignore_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
        return cls(patterns)

    def match(self, rel_path: str) -> bool:
        """Return True if the file should be ignored."""
        for pattern in self.patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # Also match against just the filename
            filename = Path(rel_path).name
            if fnmatch.fnmatch(filename, pattern.rstrip("/*")):
                return True
        return False
```

---

# ckpt/core/diff.py

```python
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
```

---

# ckpt/output/__init__.py

```python

```

---

# ckpt/output/fmt.py

```python
from datetime import datetime, timezone


def human_size(n: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} PB"


def human_date(iso: str) -> str:
    """Convert ISO date to readable local time."""
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%Y-%m-%d %H:%M")


def short_id(full_id: str) -> str:
    return full_id[:7]


def elapsed(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    return f"{seconds:.1f}s"
```

---

# ckpt/output/printer.py

```python
import sys
from contextlib import contextmanager
from typing import List, Dict

from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text

from ckpt.core.manifest import Manifest
from ckpt.output.fmt import human_size, human_date, elapsed

console = Console()
err_console = Console(stderr=True, style="red")


@contextmanager
def spinner(message: str):
    with console.status(f"[dim]{message}[/dim]", spinner="dots"):
        yield


def saved(m: Manifest, stats: Dict):
    size_stored = human_size(stats["stored_bytes"])
    size_total = human_size(stats["total_bytes"])
    t = elapsed(stats["elapsed"])
    console.print(
        f"  [green]✓[/green] [bold]{m.short_id}[/bold]  "
        f"{stats['file_count']} files · {size_total} scanned · "
        f"{size_stored} stored  [dim]({t})[/dim]"
    )


def restored(m: Manifest):
    console.print(
        f"  [green]✓[/green] restored [bold]{m.short_id}[/bold]  "
        f"[dim]\"{m.message}\"[/dim]"
    )


def exported(m: Manifest, path: str, size: int):
    console.print(
        f"  [green]✓[/green] exported [bold]{m.short_id}[/bold]  "
        f"→ {path}  [dim]({human_size(size)})[/dim]"
    )


def dry_run(m: Manifest):
    console.print(f"\n[bold]Dry run — would restore:[/bold] {m.short_id}  \"{m.message}\"")
    console.print(f"  Files: {len(m.entries)}")
    console.print(f"  Date:  {human_date(m.created_at)}")
    console.print("\n[dim]Run without --dry-run to actually restore.[/dim]")


def list_checkpoints(manifests: List[Manifest]):
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
    table.add_column("ID",      style="bold cyan", no_wrap=True)
    table.add_column("DATE",    style="dim",        no_wrap=True)
    table.add_column("MESSAGE", no_wrap=False)
    table.add_column("FILES",   justify="right",    style="dim")
    table.add_column("SIZE",    justify="right",    style="dim")
    table.add_column("TAGS",    style="yellow")

    for m in manifests:
        total = sum(e["size"] for e in m.entries)
        tags = ", ".join(m.tags) if m.tags else ""
        table.add_row(
            m.short_id,
            human_date(m.created_at),
            m.message,
            str(len(m.entries)),
            human_size(total),
            tags,
        )

    console.print(table)


def diff(m_a: Manifest, m_b: Manifest, changes: List[Dict]):
    if not changes:
        console.print(f"  [dim]No changes between {m_a.short_id} and {m_b.short_id}[/dim]")
        return

    console.print(f"\n  [dim]{m_a.short_id}[/dim] → [bold]{m_b.short_id}[/bold]\n")

    STATUS_COLOR = {"M": "yellow", "A": "green", "D": "red"}

    for c in changes:
        color = STATUS_COLOR[c["status"]]
        size_note = ""
        if c["status"] == "M":
            delta = c["size_b"] - c["size_a"]
            sign = "+" if delta >= 0 else ""
            size_note = f"  [dim]Δ{sign}{human_size(abs(delta))}[/dim]"

        console.print(
            f"  [{color}]{c['status']}[/{color}]  {c['path']}{size_note}"
        )

    console.print(f"\n  [dim]{len(changes)} change(s)[/dim]")


def info(message: str):
    console.print(f"  [dim]{message}[/dim]")


def error(message: str):
    err_console.print(f"  ✗ {message}")
```

---

# pyproject.toml

```toml
[project]
name = "ckpt"
version = "1.0.0"
description = "Dead-simple CLI checkpoint and rollback tool for EDA projects"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }

dependencies = [
    "click>=8.1",
    "rich>=13.0",
]

[project.scripts]
ckpt = "ckpt.cli:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["ckpt"]
```

---

# ckpt.spec

```python
# PyInstaller spec — run: pyinstaller ckpt.spec --clean
# Produces a single binary in dist/ckpt

block_cipher = None

a = Analysis(
    ["ckpt/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        "click",
        "rich",
        "rich.console",
        "rich.table",
        "rich.text",
        "rich.box",
        "rich.status",
        "rich.spinner",
    ],
    excludes=[
        "tkinter",
        "unittest",
        "email",
        "http",
        "urllib",
        "xml",
        "pydoc",
        "doctest",
        "difflib",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="ckpt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    onefile=True,
)
```

---

# build.sh

```bash
#!/usr/bin/env bash
# Build ckpt as a single binary using PyInstaller
# Run on each target OS: Linux, macOS, Windows (WSL2)

set -e

echo "==> Installing dependencies..."
pip install --upgrade pip
pip install click rich pyinstaller

echo "==> Building binary..."
pyinstaller ckpt.spec --clean --noconfirm

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

BINARY="dist/ckpt"
OUTPUT="dist/ckpt-${OS}-${ARCH}"

mv "$BINARY" "$OUTPUT"
echo "==> Done: $OUTPUT"
echo "    Size: $(du -sh $OUTPUT | cut -f1)"
echo ""
echo "    Install: sudo cp $OUTPUT /usr/local/bin/ckpt"
```

---

# .ckptignore

```
# ckpt ignore file — works like .gitignore
# Lines starting with # are comments

# ---- Vivado ----
*.cache/
*.ip_user_files/
*.sim/
*.hbs
*.jou
*.log
vivado_*.backup.jou
vivado_*.backup.log
# Keep DCPs — these are the valuable checkpoints
# *.dcp   <-- do NOT ignore

# ---- Quartus ----
db/
incremental_db/
*.rpt
*.pin
*.smsg
*.summary
*.done
*.qws

# ---- ModelSim / Questa ----
work/
transcript
vsim.wlf
*.wlf

# ---- Synopsys ----
*.pvl
*.syn
*.mr
alib-52/

# ---- General ----
__pycache__/
*.pyc
*.pyo
.DS_Store
Thumbs.db
*.swp
*.swo
*~
```

---

# scripts/install.sh

```bash
#!/usr/bin/env sh
# curl -fsSL https://ckpt.sh/install | sh
# Detects OS and architecture, downloads the right binary

set -e

REPO="https://github.com/yourname/ckpt/releases/latest/download"
INSTALL_DIR="/usr/local/bin"
BINARY="ckpt"

OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Normalise arch names
case "$ARCH" in
    x86_64)  ARCH="x86_64" ;;
    arm64)   ARCH="arm64"  ;;
    aarch64) ARCH="arm64"  ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

case "$OS" in
    linux | darwin) ;;
    *)
        echo "Unsupported OS: $OS. Use WSL2 on Windows."
        exit 1
        ;;
esac

URL="${REPO}/ckpt-${OS}-${ARCH}"
TMP=$(mktemp)

echo "==> Downloading ckpt for ${OS}/${ARCH}..."
curl -fsSL "$URL" -o "$TMP"
chmod +x "$TMP"

echo "==> Installing to ${INSTALL_DIR}/ckpt ..."
if [ -w "$INSTALL_DIR" ]; then
    mv "$TMP" "${INSTALL_DIR}/${BINARY}"
else
    sudo mv "$TMP" "${INSTALL_DIR}/${BINARY}"
fi

echo "==> Done. Run: ckpt --version"
```

---

# scripts/ckpt.tcl

```tcl
# Vivado TCL integration for ckpt
# Source this in your Vivado TCL console or add to your project TCL script:
#   source scripts/ckpt.tcl
#
# Then use:
#   ckpt_save "after synthesis"
#   ckpt_list
#   ckpt_restore 9e1b3ac

proc ckpt_save { message } {
    set cmd "ckpt save \"$message\""
    puts "==> $cmd"
    exec sh -c $cmd >@stdout 2>@stderr
}

proc ckpt_list {} {
    exec sh -c "ckpt list" >@stdout 2>@stderr
}

proc ckpt_restore { id } {
    set cmd "ckpt restore $id"
    puts "==> $cmd"
    exec sh -c $cmd >@stdout 2>@stderr
}

# Auto-save hook — call after key run steps
proc ckpt_after_synth {} {
    ckpt_save "post-synthesis [clock format [clock seconds] -format {%Y%m%d-%H%M}]"
}

proc ckpt_after_impl {} {
    ckpt_save "post-implementation [clock format [clock seconds] -format {%Y%m%d-%H%M}]"
}

puts "ckpt TCL integration loaded. Commands: ckpt_save, ckpt_list, ckpt_restore"
```

---

# tests/test_snapshot.py

```python
import tempfile
from pathlib import Path
from ckpt.core.snapshot import take, sha256_stream


def test_snapshot_basic():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "top.v").write_text("module top(); endmodule")
        (p / "constraints.xdc").write_text("set_property PACKAGE_PIN A1 [get_ports clk]")

        entries = take(root=tmp)
        assert len(entries) == 2
        paths = [e["path"] for e in entries]
        assert "top.v" in paths
        assert "constraints.xdc" in paths


def test_dedup_same_file():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        content = b"same content"
        (p / "a.v").write_bytes(content)
        (p / "b.v").write_bytes(content)

        entries = take(root=tmp)
        hashes = [e["hash"] for e in entries]
        assert hashes[0] == hashes[1]  # same hash for identical files


def test_ignore_ckpt_dir():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "top.v").write_text("module top(); endmodule")
        (p / ".ckpt").mkdir()
        (p / ".ckpt" / "HEAD").write_text("abc123")

        entries = take(root=tmp)
        paths = [e["path"] for e in entries]
        assert not any(".ckpt" in path for path in paths)
```

---

# tests/test_roundtrip.py

```python
import tempfile
from pathlib import Path
from ckpt.core import snapshot, store, manifest


def test_save_and_restore():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)

        # Create project files
        (p / "top.v").write_text("module top(); endmodule")
        (p / "constraints.xdc").write_text("set_property PACKAGE_PIN A1 [get_ports clk]")

        # Snapshot + save
        entries = snapshot.take(root=tmp)
        oid, stats = store.write(entries, root=tmp)
        m = manifest.create(oid, "initial save", entries, stats)
        manifest.save(m, root=tmp)

        # Modify a file
        (p / "top.v").write_text("module top(); // BROKEN endmodule")

        # Restore
        loaded = manifest.load_by_id(oid[:7], root=tmp)
        assert loaded is not None
        store.restore(loaded, root=tmp)

        # Verify restored content
        restored = (p / "top.v").read_text()
        assert "BROKEN" not in restored
        assert "module top();" in restored


def test_list_manifests():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "top.v").write_text("v1")

        entries = snapshot.take(root=tmp)
        oid, stats = store.write(entries, root=tmp)
        m = manifest.create(oid, "first checkpoint", entries, stats)
        manifest.save(m, root=tmp)

        all_m = manifest.load_all(root=tmp)
        assert len(all_m) == 1
        assert all_m[0].message == "first checkpoint"
```
