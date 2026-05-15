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
