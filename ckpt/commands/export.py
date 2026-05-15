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
