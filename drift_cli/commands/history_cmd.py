"""History, undo, again, and cleanup commands."""

from pathlib import Path

import typer
from rich.console import Console

from drift_cli.core.history import HistoryManager
from drift_cli.ui.display import DriftUI

console = Console()

history_app = typer.Typer()


@history_app.command("history")
def history(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of entries to show"),
):
    """View Drift command history."""
    hist = HistoryManager()
    entries = hist.get_history(limit=limit)

    console.print()
    DriftUI.show_history(entries)


@history_app.command("again")
def again():
    """Re-run the last Drift command."""
    from drift_cli.commands.suggest_cmd import suggest

    hist = HistoryManager()
    last = hist.get_last_entry()

    if not last:
        DriftUI.show_error("No previous command found")
        raise typer.Exit(1)

    DriftUI.show_info(f"Re-running: {last.query}")
    console.print()
    suggest(query=last.query, execute=False, dry_run=False)


@history_app.command("undo")
def undo():
    """Restore files from the last operation."""
    hist = HistoryManager()
    last = hist.get_last_entry()

    if not last or not last.executed:
        DriftUI.show_error("No executed command to undo")
        raise typer.Exit(1)

    if not last.snapshot_id:
        DriftUI.show_error("No snapshot available for this command")
        raise typer.Exit(1)

    DriftUI.show_warning(f"This will restore files to their state before: {last.query}")
    console.print()

    if typer.confirm("Proceed with undo?"):
        success = hist.restore_snapshot(last.snapshot_id)
        if success:
            DriftUI.show_success("Files restored successfully")
        else:
            DriftUI.show_error("Failed to restore files")
            raise typer.Exit(1)
    else:
        DriftUI.show_info("Undo cancelled")


@history_app.command("cleanup")
def cleanup(
    keep: int = typer.Option(50, "--keep", "-k", help="Recent snapshots to keep"),
    days: int = typer.Option(30, "--days", "-d", help="Max snapshot age in days"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Skip confirmation"),
):
    """Clean up old snapshots and free disk space."""
    hist = HistoryManager()
    snapshots_dir = Path.home() / ".drift" / "snapshots"

    if not snapshots_dir.exists():
        DriftUI.show_info("No snapshots to clean up")
        return

    total_size = sum(f.stat().st_size for f in snapshots_dir.rglob("*") if f.is_file())
    total_mb = total_size / (1024 * 1024)
    snapshot_count = len(list(snapshots_dir.iterdir()))
    console.print(f"[cyan]Snapshots: {snapshot_count} ({total_mb:.1f} MB)[/cyan]")

    if not auto:
        if not typer.confirm(f"Delete snapshots older than {days} days (keep {keep})?"):
            return

    deleted = hist.cleanup_old_snapshots(keep=keep, max_age_days=days)

    if deleted > 0:
        new_size = sum(f.stat().st_size for f in snapshots_dir.rglob("*") if f.is_file())
        freed = total_mb - new_size / (1024 * 1024)
        DriftUI.show_success(f"Deleted {deleted} snapshots, freed {freed:.1f} MB")
    else:
        DriftUI.show_info("Nothing to clean up")
