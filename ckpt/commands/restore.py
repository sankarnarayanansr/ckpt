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
