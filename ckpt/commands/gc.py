import click
from pathlib import Path
from ckpt.core import manifest
from ckpt.output import printer, fmt

@click.command()
@click.option("--root", default=".")
@click.option("--dry-run", is_flag=True)
def cmd(root, dry_run):
    """Remove objects not referenced by any checkpoint.

    Safe to run anytime. Use after: ckpt delete --all
    """
    manifests = manifest.load_all(root=root)

    # Collect all hashes still referenced
    live = {e["hash"] for m in manifests for e in m.entries}

    obj_root = Path(root) / ".ckpt" / "objects"
    freed = 0
    freed_bytes = 0

    for obj in obj_root.rglob("*"):
        if not obj.is_file(): continue
        hash_str = obj.parent.name + obj.name
        if hash_str not in live:
            freed_bytes += obj.stat().st_size
            freed += 1
            if not dry_run:
                obj.unlink()

    action = "Would free" if dry_run else "Freed"
    printer.info(f"{action} {freed} object(s)  ({fmt.human_size(freed_bytes)})")