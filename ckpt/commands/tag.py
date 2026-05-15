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
