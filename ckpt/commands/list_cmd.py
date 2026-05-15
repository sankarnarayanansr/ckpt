import click
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
