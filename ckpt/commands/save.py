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
