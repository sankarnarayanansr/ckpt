import click
from ckpt.commands import save, restore, list_cmd, diff, tag, export,delete,gc

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
cli.add_command(delete.cmd,  "delete")
cli.add_command(gc.cmd,      "gc")