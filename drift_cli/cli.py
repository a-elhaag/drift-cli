"""Main CLI application using Typer."""

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from drift_cli.commands.memory_cmd import memory_app
from drift_cli.core.auto_setup import ensure_ollama_ready
from drift_cli.core.config import ConfigManager
from drift_cli.core.executor import Executor
from drift_cli.core.first_run import is_first_run, run_setup_wizard
from drift_cli.core.history import HistoryManager
from drift_cli.core.memory import MemoryManager
from drift_cli.core.ollama import OllamaClient
from drift_cli.core.safety import SafetyChecker
from drift_cli.core.slash_commands import SlashCommandHandler
from drift_cli.ui.display import DriftUI

app = typer.Typer(
    name="drift",
    help="Terminal-native, safety-first AI assistant",
    add_completion=False,
    invoke_without_command=True,
)

# Add memory subcommand
app.add_typer(memory_app, name="memory")

console = Console()


@app.callback()
def main(ctx: typer.Context):
    """Drift — terminal-native, safety-first AI assistant."""
    # First-run setup wizard
    if is_first_run():
        run_setup_wizard()
        if ctx.invoked_subcommand is None:
            raise typer.Exit(0)

    # If no subcommand given, show help
    if ctx.invoked_subcommand is None:
        _show_help()
        raise typer.Exit(0)


def get_config() -> ConfigManager:
    """Get the configuration manager."""
    return ConfigManager()


def get_ollama_client() -> OllamaClient:
    """Get an Ollama client instance."""
    config = get_config().load()
    model = os.getenv("DRIFT_MODEL", config.model)
    return OllamaClient(base_url=config.ollama_url, model=model)


def check_ollama():
    """Ensure Ollama is ready, using auto-setup config settings."""
    config = get_config().load()
    model = os.getenv("DRIFT_MODEL", config.model)

    ready = ensure_ollama_ready(
        model=model,
        base_url=config.ollama_url,
        auto_install=config.auto_install_ollama,
        auto_start=config.auto_start_ollama,
        auto_pull=config.auto_pull_model,
    )

    if not ready:
        console.print()
        console.print("[bold]To fix manually:[/bold]")
        console.print("  1. Install Ollama → https://ollama.com")
        console.print("  2. Start Ollama   → ollama serve")
        console.print(f"  3. Pull model     → ollama pull {model}")
        raise typer.Exit(1)


def _auto_cleanup_snapshots():
    """Silently clean up snapshots if there are too many."""
    try:
        snapshots_dir = Path.home() / ".drift" / "snapshots"
        if not snapshots_dir.exists():
            return
        snapshot_count = sum(1 for d in snapshots_dir.iterdir() if d.is_dir())
        if snapshot_count > 100:
            HistoryManager().cleanup_old_snapshots(keep=50, max_age_days=30)
    except Exception:
        pass


@app.command()
def suggest(
    query: str = typer.Argument(..., help="Natural language query or slash command"),
    execute: bool = typer.Option(
        False, "--execute", "-e", help="Execute immediately without confirmation"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Show dry-run only, don't execute"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed explanation"
    ),
    no_memory: bool = typer.Option(
        False, "--no-memory", help="Disable memory/personalization for this query"
    ),
):
    """Get AI-powered command suggestions from natural language."""
    _auto_cleanup_snapshots()

    memory = None if no_memory else MemoryManager()
    if memory:
        memory.update_context(query=query)

    # Handle slash commands
    slash_handler = SlashCommandHandler(memory=memory)
    is_slash, enhanced_query, error = slash_handler.process_slash_command(query)

    if is_slash:
        if query.strip().lower() == "/help":
            console.print(slash_handler.get_help_text())
            return
        if error:
            DriftUI.show_error(error)
            raise typer.Exit(1)
        query = enhanced_query

    check_ollama()

    client = get_ollama_client()
    executor = Executor()
    history = HistoryManager()

    try:
        context = executor.get_context()

        # Silently enhance context with memory (no noisy output)
        if memory:
            context = memory.enhance_prompt_with_context(context)

        # Get plan from Ollama
        from drift_cli.ui.progress import ProgressSpinner

        with ProgressSpinner("Thinking..."):
            plan = client.get_plan(query, context)

        # Handle clarification
        if plan.clarification_needed:
            answers = DriftUI.ask_clarification(plan.clarification_needed)
            clarification_context = f"{context}\n\nClarifications:\n"
            for idx, answer in answers.items():
                clarification_context += f"Q: {plan.clarification_needed[idx].question}\nA: {answer}\n"
            with ProgressSpinner("Re-analyzing..."):
                plan = client.get_plan(query, clarification_context)

        # Display plan (explanation only with --verbose)
        DriftUI.show_plan(plan, query, show_explanation=verbose)

        # Safety check
        commands_list = [cmd.command for cmd in plan.commands]
        all_safe, warnings = SafetyChecker.validate_commands(commands_list)

        if warnings:
            for warning in warnings:
                console.print(warning)

        if not all_safe:
            DriftUI.show_error("Commands blocked for safety. Aborting.")
            history.add_entry(query, plan, executed=False)
            raise typer.Exit(1)

        # Execute or confirm
        if dry_run:
            DriftUI.show_info("Dry-run mode — no commands executed")
            exit_code, output, _ = executor.execute_plan(plan, dry_run=True)
            if output:
                console.print(output)
            history.add_entry(query, plan, executed=False)
            if memory:
                memory.learn_from_execution(plan, executed=False, success=False)

        elif execute or DriftUI.confirm_execution(plan.risk):
            exit_code, output, snapshot_id = executor.execute_plan(plan, dry_run=False)
            console.print()
            DriftUI.show_execution_result(exit_code, output)
            history.add_entry(query, plan, executed=True, exit_code=exit_code, snapshot_id=snapshot_id)
            if memory:
                memory.learn_from_execution(plan, executed=True, success=(exit_code == 0))
            if snapshot_id and exit_code == 0:
                console.print(f"[dim]Snapshot: {snapshot_id[:8]}… (drift undo to rollback)[/dim]")
        else:
            DriftUI.show_info("Cancelled")
            history.add_entry(query, plan, executed=False)
            if memory:
                memory.learn_from_execution(plan, executed=False, success=False)

    except ValueError as e:
        DriftUI.show_error(str(e))
        raise typer.Exit(1)
    finally:
        client.close()


@app.command()
def find(query: str = typer.Argument(..., help="What to find")):
    """Smart file and content search."""
    find_query = f"Find: {query}. Use safe read-only commands like 'find', 'rg', 'grep', 'fd', or 'ls'. Do not modify any files."
    suggest(query=find_query, execute=False, dry_run=False, verbose=False)


@app.command()
def explain(command: str = typer.Argument(..., help="Command to explain")):
    """Explain what a shell command does."""
    check_ollama()
    client = get_ollama_client()
    try:
        explanation = client.explain_command(command)
        console.print()
        console.print(explanation)
    except ValueError as e:
        DriftUI.show_error(str(e))
        raise typer.Exit(1)
    finally:
        client.close()


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of entries to show")
):
    """View Drift command history."""
    hist = HistoryManager()
    entries = hist.get_history(limit=limit)

    console.print()
    DriftUI.show_history(entries)


@app.command()
def again():
    """Re-run the last Drift command."""
    hist = HistoryManager()
    last = hist.get_last_entry()

    if not last:
        DriftUI.show_error("No previous command found")
        raise typer.Exit(1)

    DriftUI.show_info(f"Re-running: {last.query}")
    console.print()
    suggest(query=last.query, execute=False, dry_run=False)


@app.command()
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


@app.command()
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


@app.command()
def doctor():
    """Diagnose and fix common issues."""
    from drift_cli.core.auto_setup import (
        install_ollama, is_model_available, is_ollama_installed,
        is_ollama_running, pull_model, start_ollama,
    )

    console.print("[bold cyan]Drift Doctor[/bold cyan]\n")

    config = get_config().load()
    model = os.getenv("DRIFT_MODEL", config.model)
    ok = True

    # Ollama binary
    if is_ollama_installed():
        DriftUI.show_success("Ollama installed")
    elif config.auto_install_ollama:
        ok = install_ollama() or False
    else:
        ok = False
        DriftUI.show_error("Ollama not installed → https://ollama.com")

    # Ollama server
    if is_ollama_installed():
        if is_ollama_running(config.ollama_url):
            DriftUI.show_success("Ollama running")
        elif config.auto_start_ollama:
            if not start_ollama(config.ollama_url):
                ok = False
        else:
            ok = False
            DriftUI.show_warning("Ollama not running → ollama serve")

    # Model
    if is_ollama_installed() and is_ollama_running(config.ollama_url):
        if is_model_available(model, config.ollama_url):
            DriftUI.show_success(f"Model {model} ready")
        elif config.auto_pull_model:
            if not pull_model(model, config.ollama_url):
                ok = False
        else:
            ok = False
            DriftUI.show_warning(f"Model {model} missing → ollama pull {model}")

    # Drift directory
    drift_dir = Path.home() / ".drift"
    if drift_dir.exists():
        DriftUI.show_success(f"Config: {drift_dir}")
    else:
        DriftUI.show_warning("No ~/.drift directory")

    console.print()
    if ok:
        console.print("[bold green]All checks passed[/bold green]")
    else:
        console.print("[yellow]Some issues remain — see above[/yellow]")


@app.command()
def version():
    """Show Drift CLI version."""
    from drift_cli import __version__

    console.print(f"Drift CLI v{__version__}")


@app.command()
def setup():
    """Re-run the first-time setup wizard."""
    run_setup_wizard()


def _show_help():
    """Show a rich help screen with all commands."""
    from drift_cli import __version__

    console.print(f"\n[bold cyan]Drift CLI[/bold cyan] [dim]v{__version__}[/dim]")
    console.print("[dim]Terminal-native, safety-first AI assistant[/dim]\n")

    console.print(Panel(
        "[cyan]drift suggest[/cyan] [dim]<query>[/dim]    AI command suggestions\n"
        "[cyan]drift explain[/cyan] [dim]<cmd>[/dim]      Explain a shell command\n"
        "[cyan]drift find[/cyan] [dim]<query>[/dim]       Smart file search\n"
        "[cyan]drift history[/cyan]             View past commands\n"
        "[cyan]drift again[/cyan]               Re-run last command\n"
        "[cyan]drift undo[/cyan]                Rollback last execution\n"
        "[cyan]drift cleanup[/cyan]             Free snapshot storage\n"
        "[cyan]drift doctor[/cyan]              System health check\n"
        "[cyan]drift memory show[/cyan]         View learned preferences\n"
        "[cyan]drift setup[/cyan]               Run setup wizard\n"
        "[cyan]drift version[/cyan]             Show version",
        title="[bold]Commands[/bold]",
        border_style="cyan",
    ))

    console.print(Panel(
        "[dim]-e, --execute[/dim]    Run without confirmation\n"
        "[dim]-d, --dry-run[/dim]    Preview only, don't execute\n"
        "[dim]-v, --verbose[/dim]    Show detailed explanation\n"
        "[dim]--no-memory[/dim]      Disable personalization",
        title="[bold]Suggest Flags[/bold]",
        border_style="dim",
    ))
    console.print()


if __name__ == "__main__":
    app()
