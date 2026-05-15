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
