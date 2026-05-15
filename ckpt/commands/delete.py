import click
from ckpt.core import manifest, store
from ckpt.output import printer

@click.command()
@click.option("--checkpoint","checkpoint_id",help="Delete particular checkpoint")
@click.option("--all", "delete_all", is_flag=True, help="Delete ALL checkpoints")
@click.option("--root", default=".")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def cmd(checkpoint_id, delete_all, root, yes):
    """Delete one checkpoint or all checkpoints.

    ckpt delete 9e1b3ac
    ckpt delete --all
    """
    if delete_all:
        manifests = manifest.load_all(root=root)
        if not manifests:
            printer.info("No checkpoints to delete.")
            return
        if not yes:
            click.confirm(
                f"Delete all {len(manifests)} checkpoints? This cannot be undone.",
                abort=True
            )
        for m in manifests:
            manifest.delete(m, root=root)
        printer.info(f"Deleted {len(manifests)} checkpoint(s). Run: ckpt gc")
    else:
        m = manifest.load_by_id(checkpoint_id, root=root)
        if m is None:
            printer.error(f"Checkpoint '{checkpoint_id}' not found.")
            raise click.Abort()
        manifest.delete(m, root=root)
        printer.info(f"Deleted {m.short_id}  \"{m.message}\"")