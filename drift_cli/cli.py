"""Main CLI application using Typer."""

import os
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from drift_cli.commands.memory_cmd import memory_app
from drift_cli.core.auto_setup import ensure_ollama_ready
from drift_cli.core.config import ConfigManager, DriftConfig
from drift_cli.core.executor import Executor
from drift_cli.core.first_run import is_first_run, run_setup_wizard
from drift_cli.core.history import HistoryManager
from drift_cli.core.memory import MemoryManager
from drift_cli.core.ollama import OllamaClient
from drift_cli.core.safety import SafetyChecker
from drift_cli.core.slash_commands import SlashCommandHandler
from drift_cli.ui.display import DriftUI

# Known subcommands for argv preprocessing
_SUBCOMMANDS = {
    "suggest", "find", "explain", "history", "again", "undo",
    "cleanup", "doctor", "config", "uninstall", "version", "setup", "memory",
}

# Subcommands that accept a free-text query as their first positional arg
_QUERY_SUBCOMMANDS = {"suggest", "find", "explain"}


def _preprocess_argv():
    """Normalize sys.argv so multi-word queries work without quotes.

    Handles three cases:
      1. drift list all files        → drift suggest "list all files"
      2. drift find js files          → drift find "js files"
      3. drift suggest -d list files  → drift suggest -d "list files"
    """
    args = sys.argv[1:]
    if not args:
        return

    # Case 1: first non-option arg is NOT a known subcommand
    #         → treat everything as a query for 'suggest'
    first = args[0]
    if not first.startswith("-") and first not in _SUBCOMMANDS:
        query = " ".join(args)
        sys.argv = [sys.argv[0], "suggest", query]
        return

    # Case 2 & 3: subcommand that takes a query + multiple trailing words
    if first in _QUERY_SUBCOMMANDS and len(args) > 1:
        options = [a for a in args[1:] if a.startswith("-")]
        positional = [a for a in args[1:] if not a.startswith("-")]
        if len(positional) > 1:
            query = " ".join(positional)
            sys.argv = [sys.argv[0], first] + options + [query]


app = typer.Typer(
    name="drift",
    help="Terminal-native, safety-first AI assistant",
    add_completion=False,
    invoke_without_command=True,
)

# Add memory subcommand
app.add_typer(memory_app, name="memory")

console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Drift — terminal-native, safety-first AI assistant."""
    # First-run setup wizard
    if is_first_run():
        run_setup_wizard()
        if ctx.invoked_subcommand is None:
            raise typer.Exit(0)

    # No subcommand → show help (queries are rewritten to 'suggest' by _preprocess_argv)
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
                clarification_context += (
                    f"Q: {plan.clarification_needed[idx].question}\nA: {answer}\n"
                )
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
            history.add_entry(
                query, plan, executed=True, exit_code=exit_code, snapshot_id=snapshot_id
            )
            if memory:
                memory.learn_from_execution(
                    plan, executed=True, success=(exit_code == 0)
                )
            if snapshot_id and exit_code == 0:
                console.print(
                    f"[dim]Snapshot: {snapshot_id[:8]}… (drift undo to rollback)[/dim]"
                )
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
        new_size = sum(
            f.stat().st_size for f in snapshots_dir.rglob("*") if f.is_file()
        )
        freed = total_mb - new_size / (1024 * 1024)
        DriftUI.show_success(f"Deleted {deleted} snapshots, freed {freed:.1f} MB")
    else:
        DriftUI.show_info("Nothing to clean up")


@app.command()
def doctor():
    """Diagnose and fix common issues."""
    from drift_cli.core.auto_setup import (
        install_ollama,
        is_model_available,
        is_ollama_installed,
        is_ollama_running,
        pull_model,
        start_ollama,
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
def config():
    """View and change Drift settings interactively."""
    from rich.prompt import Confirm, Prompt

    cm = get_config()
    cfg = cm.load()

    console.print("[bold cyan]Drift Settings[/bold cyan]\n")
    console.print(f"  [cyan]model[/cyan]          = {cfg.model}")
    console.print(f"  [cyan]ollama_url[/cyan]     = {cfg.ollama_url}")
    console.print(f"  [cyan]temperature[/cyan]    = {cfg.temperature}")
    console.print(f"  [cyan]max_history[/cyan]    = {cfg.max_history}")
    console.print(
        f"  [cyan]auto_install[/cyan]   = {'ON' if cfg.auto_install_ollama else 'OFF'}"
    )
    console.print(
        f"  [cyan]auto_start[/cyan]     = {'ON' if cfg.auto_start_ollama else 'OFF'}"
    )
    console.print(
        f"  [cyan]auto_pull[/cyan]      = {'ON' if cfg.auto_pull_model else 'OFF'}"
    )
    console.print(
        f"  [cyan]auto_snapshot[/cyan]  = {'ON' if cfg.auto_snapshot else 'OFF'}"
    )
    console.print()

    if not Confirm.ask("Edit settings?", default=False):
        return

    console.print("[dim]Press Enter to keep current value[/dim]\n")

    new_model = Prompt.ask("Model", default=cfg.model)
    new_url = Prompt.ask("Ollama URL", default=cfg.ollama_url)
    new_temp = Prompt.ask("Temperature (0.0–1.0)", default=str(cfg.temperature))
    new_hist = Prompt.ask("Max history entries", default=str(cfg.max_history))
    new_auto_install = Confirm.ask(
        "Auto-install Ollama?", default=cfg.auto_install_ollama
    )
    new_auto_start = Confirm.ask("Auto-start Ollama?", default=cfg.auto_start_ollama)
    new_auto_pull = Confirm.ask("Auto-pull model?", default=cfg.auto_pull_model)
    new_snapshot = Confirm.ask(
        "Auto-snapshot before execution?", default=cfg.auto_snapshot
    )

    cm.save(
        DriftConfig(
            model=new_model,
            ollama_url=new_url,
            temperature=float(new_temp),
            top_p=cfg.top_p,
            max_history=int(new_hist),
            auto_snapshot=new_snapshot,
            auto_install_ollama=new_auto_install,
            auto_start_ollama=new_auto_start,
            auto_pull_model=new_auto_pull,
        )
    )
    DriftUI.show_success("Settings saved to ~/.drift/config.json")


@app.command()
def uninstall():
    """Uninstall Drift CLI and clean up all data."""
    import shutil
    import subprocess

    console.print("[bold red]Drift Uninstaller[/bold red]\n")
    console.print("This will remove:")
    console.print("  1. drift-cli Python package")
    console.print("  2. ~/.drift directory (config, history, snapshots)")
    console.print()

    if not typer.confirm("Proceed with uninstall?", default=False):
        DriftUI.show_info("Cancelled")
        return

    # Remove ~/.drift
    drift_dir = Path.home() / ".drift"
    if drift_dir.exists():
        shutil.rmtree(drift_dir)
        DriftUI.show_success("Removed ~/.drift")
    else:
        console.print("[dim]  ~/.drift not found (skipped)[/dim]")

    # Offer to uninstall Ollama
    from drift_cli.core.auto_setup import is_ollama_installed

    if is_ollama_installed():
        console.print()
        if typer.confirm("Also uninstall Ollama?", default=False):
            import platform

            system = platform.system().lower()

            try:
                if system == "darwin":
                    # Stop Ollama
                    subprocess.run(["pkill", "-f", "Ollama"], capture_output=True)
                    # Remove app bundle
                    app_path = Path("/Applications/Ollama.app")
                    if app_path.exists():
                        shutil.rmtree(app_path)
                    # Remove binary (brew or manual)
                    for p in ["/usr/local/bin/ollama", str(Path.home() / ".ollama")]:
                        path = Path(p)
                        if path.exists():
                            if path.is_dir():
                                shutil.rmtree(path)
                            else:
                                path.unlink()
                    DriftUI.show_success("Ollama removed")
                elif system == "linux":
                    subprocess.run(
                        ["sudo", "rm", "-f", "/usr/local/bin/ollama"],
                        capture_output=True,
                    )
                    shutil.rmtree(Path.home() / ".ollama", ignore_errors=True)
                    DriftUI.show_success("Ollama removed")
                else:
                    DriftUI.show_warning(f"Manual Ollama removal needed on {system}")
            except Exception as e:
                DriftUI.show_warning(f"Ollama removal incomplete: {e}")
        else:
            console.print("[dim]  Ollama kept[/dim]")

    # Uninstall drift-cli package
    console.print()
    console.print("[yellow]To finish, run:[/yellow]")
    console.print("  [cyan]pip uninstall drift-cli[/cyan]")
    console.print()


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

    console.print(
        Panel(
            '[cyan]drift[/cyan] [dim]"list large files"[/dim]     Quick shortcut (same as suggest)\n'
            "[cyan]drift suggest[/cyan] [dim]<query>[/dim]       AI command suggestions\n"
            "[cyan]drift explain[/cyan] [dim]<cmd>[/dim]         Explain a shell command\n"
            "[cyan]drift find[/cyan] [dim]<query>[/dim]          Smart file search\n"
            "[cyan]drift history[/cyan]                View past commands\n"
            "[cyan]drift again[/cyan]                  Re-run last command\n"
            "[cyan]drift undo[/cyan]                   Rollback last execution\n"
            "[cyan]drift config[/cyan]                 View/edit settings\n"
            "[cyan]drift doctor[/cyan]                 System health check\n"
            "[cyan]drift cleanup[/cyan]                Free snapshot storage\n"
            "[cyan]drift memory show[/cyan]            View learned preferences\n"
            "[cyan]drift setup[/cyan]                  Run setup wizard\n"
            "[cyan]drift uninstall[/cyan]              Remove Drift & data\n"
            "[cyan]drift version[/cyan]                Show version",
            title="[bold]Commands[/bold]",
            border_style="cyan",
        )
    )

    console.print(
        Panel(
            "[cyan]/git[/cyan]    Next git action     [cyan]/commit[/cyan]  Smart commit\n"
            "[cyan]/find[/cyan]   Search files        [cyan]/fix[/cyan]     Fix recent errors\n"
            "[cyan]/test[/cyan]   Run project tests   [cyan]/build[/cyan]   Build project\n"
            "[cyan]/dev[/cyan]    Start dev server    [cyan]/clean[/cyan]   Clean artifacts\n"
            "[cyan]/deps[/cyan]   Check dependencies  [cyan]/lint[/cyan]    Run linter\n"
            "[cyan]/tree[/cyan]   Directory tree      [cyan]/tips[/cyan]    Workflow tips\n"
            '\n[dim]Usage: drift "/git" or drift suggest "/commit"[/dim]',
            title="[bold]Slash Commands[/bold]",
            border_style="yellow",
        )
    )

    console.print(
        Panel(
            "[dim]-e, --execute[/dim]    Run without confirmation\n"
            "[dim]-d, --dry-run[/dim]    Preview only, don't execute\n"
            "[dim]-v, --verbose[/dim]    Show detailed explanation\n"
            "[dim]--no-memory[/dim]      Disable personalization",
            title="[bold]Flags (for suggest)[/bold]",
            border_style="dim",
        )
    )
    console.print()


def main_entry():
    """Entry point that preprocesses argv, then runs the Typer app."""
    _preprocess_argv()
    app()


if __name__ == "__main__":
    main_entry()
