"""Main CLI application using Typer."""

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from drift_cli.commands.memory_cmd import memory_app
from drift_cli.core.auto_setup import ensure_ollama_ready
from drift_cli.core.config import ConfigManager
from drift_cli.core.executor import Executor
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
)

# Add memory subcommand
app.add_typer(memory_app, name="memory")

console = Console()


def get_config() -> ConfigManager:
    """Get the configuration manager."""
    return ConfigManager()


def get_ollama_client() -> OllamaClient:
    """Get an Ollama client instance."""
    config = get_config().load()
    model = os.getenv("DRIFT_MODEL", config.model)
    return OllamaClient(base_url=config.ollama_url, model=model)


def check_ollama():
    """Ensure Ollama is installed, running, and has the required model.

    Respects auto_install_ollama, auto_start_ollama, and auto_pull_model
    settings from ~/.drift/config.json. When enabled, missing prerequisites
    are resolved automatically.
    """
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
        console.print("1. [cyan]Install Ollama[/cyan]: https://ollama.com")
        console.print("2. [cyan]Start Ollama[/cyan]: ollama serve")
        console.print(f"3. [cyan]Pull the model[/cyan]: ollama pull {model}")
        console.print()
        console.print("[dim]To toggle auto-setup, edit ~/.drift/config.json:[/dim]")
        console.print(
            "[dim]  auto_install_ollama, auto_start_ollama, auto_pull_model[/dim]"
        )
        console.print()
        raise typer.Exit(1)


def auto_cleanup_snapshots():
    """Auto-cleanup snapshots if there are too many (silent, non-blocking)."""
    try:
        from pathlib import Path

        snapshots_dir = Path.home() / ".drift" / "snapshots"

        if not snapshots_dir.exists():
            return

        # Count snapshots
        snapshot_count = sum(1 for d in snapshots_dir.iterdir() if d.is_dir())

        # Auto-cleanup if >100 snapshots (keep 50 most recent)
        if snapshot_count > 100:
            hist = HistoryManager()
            deleted = hist.cleanup_old_snapshots(keep=50, max_age_days=30)
            # Silent cleanup, don't interrupt user
    except Exception:
        # If cleanup fails, don't break the app
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
    no_memory: bool = typer.Option(
        False, "--no-memory", help="Disable memory/personalization for this query"
    ),
):
    """Get AI-powered command suggestions from natural language.

    You can also use slash commands for quick context-aware actions:
    - /git - Suggest git actions based on repo status
    - /commit - Smart commit with AI-generated message
    - /find <pattern> - Search files and content
    - /help - Show all available slash commands
    """
    # Auto-cleanup old snapshots in background (if >100 exist)
    auto_cleanup_snapshots()

    # Initialize memory first (unless disabled)
    memory = None if no_memory else MemoryManager()

    # Update context with current working directory
    if memory:
        memory.update_context(query=query)

    # Handle slash commands
    slash_handler = SlashCommandHandler(memory=memory)
    is_slash, enhanced_query, error = slash_handler.process_slash_command(query)

    if is_slash:
        # Special handling for /help
        if query.strip().lower() == "/help":
            help_text = slash_handler.get_help_text()
            console.print(help_text)
            return

        # If there's an error (unknown command, missing requirements)
        if error:
            DriftUI.show_error(error)
            raise typer.Exit(1)

        # Replace query with enhanced version
        query = enhanced_query

        # Show what slash command was detected
        command_name = (
            query.split("\n")[0]
            if "\n" in enhanced_query
            else slash_handler.parse_slash_command(query)[0]
        )
        console.print(f"[dim]Using slash command: {command_name}[/dim]\n")

    check_ollama()

    client = get_ollama_client()
    executor = Executor()
    history = HistoryManager()

    try:
        # Get context
        context = executor.get_context()

        # Enhance context with memory insights (if enabled)
        if memory:
            context = memory.enhance_prompt_with_context(context)

            # Show personalization indicator
            if (
                not is_slash
            ):  # Don't show for slash commands (they already show context)
                smart_defaults = memory.get_smart_defaults()
                if (
                    memory.preferences.favorite_tools
                    or memory.context.detected_project_type
                ):
                    console.print("[dim]💡 Using personalized context[/dim]")

        # Get plan from Ollama
        try:
            from drift_cli.ui.progress import ProgressSpinner, show_timeout_warning

            show_timeout_warning(90)
            with ProgressSpinner("Analyzing your request..."):
                plan = client.get_plan(query, context)
        except ImportError:
            DriftUI.show_info("Analyzing your request...")
            plan = client.get_plan(query, context)

        # Show memory-enhanced suggestions before the plan
        if memory and not is_slash:
            DriftUI.show_memory_suggestions(memory, query)

        # Check if clarification is needed
        if plan.clarification_needed:
            answers = DriftUI.ask_clarification(plan.clarification_needed)
            # Re-query with clarification
            clarification_context = f"{context}\n\nClarifications:\n"
            for idx, answer in answers.items():
                question = plan.clarification_needed[idx].question
                clarification_context += f"Q: {question}\nA: {answer}\n"

            DriftUI.show_info("Re-analyzing with your input...")
            plan = client.get_plan(query, clarification_context)

        # Display the plan
        DriftUI.show_plan(plan, query)

        # Validate safety
        commands_list = [cmd.command for cmd in plan.commands]
        all_safe, warnings = SafetyChecker.validate_commands(commands_list)

        if warnings:
            console.print()
            for warning in warnings:
                console.print(warning)

        if not all_safe:
            DriftUI.show_error("Some commands are blocked for safety. Aborting.")
            history.add_entry(query, plan, executed=False)
            raise typer.Exit(1)

        # Show preview
        DriftUI.show_commands_preview(plan.commands)

        # Confirm execution (unless --execute flag is set)
        if dry_run:
            DriftUI.show_info("Dry-run mode - no commands will be executed")
            exit_code, output, _ = executor.execute_plan(plan, dry_run=True)
            console.print()
            console.print(output)
            history.add_entry(query, plan, executed=False)

            # Learn from rejection (user previewed but didn't execute)
            if memory:
                memory.learn_from_execution(plan, executed=False, success=False)
        elif execute or DriftUI.confirm_execution(plan.risk):
            # Execute
            exit_code, output, snapshot_id = executor.execute_plan(plan, dry_run=False)

            # Show results
            console.print()
            DriftUI.show_execution_result(exit_code, output)

            # Save to history
            history.add_entry(
                query, plan, executed=True, exit_code=exit_code, snapshot_id=snapshot_id
            )

            # Learn from execution (success or failure)
            if memory:
                memory.learn_from_execution(
                    plan, executed=True, success=(exit_code == 0)
                )

            if snapshot_id and exit_code == 0:
                DriftUI.show_info(
                    f"Snapshot saved: {snapshot_id[:8]}... (use 'drift undo' to rollback)"
                )
        else:
            DriftUI.show_info("Execution cancelled")
            history.add_entry(query, plan, executed=False)

            # Learn from rejection
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
    check_ollama()

    # Build a specialized query for find operations
    find_query = f"Find: {query}. Use safe read-only commands like 'find', 'rg', 'grep', 'fd', or 'ls'. Do not modify any files."

    suggest(query=find_query, execute=False, dry_run=False)


@app.command()
def explain(command: str = typer.Argument(..., help="Command to explain")):
    """Get a detailed explanation of a shell command."""
    check_ollama()

    client = get_ollama_client()

    try:
        DriftUI.show_info(f"Explaining: {command}")
        console.print()

        explanation = client.explain_command(command)
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
    keep: int = typer.Option(
        50, "--keep", "-k", help="Number of recent snapshots to keep"
    ),
    days: int = typer.Option(
        30, "--days", "-d", help="Delete snapshots older than this many days"
    ),
    auto: bool = typer.Option(
        False, "--auto", "-a", help="Auto-cleanup without confirmation"
    ),
):
    """Clean up old snapshots and free disk space."""
    from pathlib import Path

    hist = HistoryManager()

    # Show current disk usage
    snapshots_dir = Path.home() / ".drift" / "snapshots"
    if snapshots_dir.exists():
        total_size = sum(
            f.stat().st_size for f in snapshots_dir.rglob("*") if f.is_file()
        )
        total_size_mb = total_size / (1024 * 1024)

        console.print(
            f"\n[cyan]Current snapshot storage: {total_size_mb:.2f} MB[/cyan]"
        )

        snapshots = hist.list_snapshots()
        console.print(f"[cyan]Total snapshots: {len(snapshots)}[/cyan]\n")

    if not auto:
        console.print(
            f"[yellow]This will delete snapshots older than {days} days (keeping {keep} most recent)[/yellow]"
        )
        if not typer.confirm("Proceed with cleanup?"):
            DriftUI.show_info("Cleanup cancelled")
            raise typer.Exit(0)

    deleted = hist.cleanup_old_snapshots(keep=keep, max_age_days=days)

    if deleted > 0:
        # Calculate new size
        if snapshots_dir.exists():
            new_size = sum(
                f.stat().st_size for f in snapshots_dir.rglob("*") if f.is_file()
            )
            new_size_mb = new_size / (1024 * 1024)
            freed_mb = total_size_mb - new_size_mb

            DriftUI.show_success(f"Deleted {deleted} old snapshots")
            console.print(f"[green]Freed {freed_mb:.2f} MB of disk space[/green]")
            console.print(f"[dim]New storage: {new_size_mb:.2f} MB[/dim]")
        else:
            DriftUI.show_success(f"Deleted {deleted} old snapshots")
    else:
        DriftUI.show_info("No snapshots to clean up")


@app.command()
def doctor():
    """Diagnose and fix common terminal and environment issues."""
    console.print("[bold cyan]Drift Doctor — System Diagnostics[/bold cyan]")
    console.print()

    from drift_cli.core.auto_setup import (
        install_ollama,
        is_model_available,
        is_ollama_installed,
        is_ollama_running,
        pull_model,
        start_ollama,
    )

    config = get_config().load()
    model = os.getenv("DRIFT_MODEL", config.model)
    all_good = True

    # ── Ollama installation ──
    console.print("[bold]Checking Ollama...[/bold]")
    if is_ollama_installed():
        DriftUI.show_success("Ollama is installed")
    else:
        all_good = False
        if config.auto_install_ollama:
            console.print("[yellow]  Ollama not found — auto-installing...[/yellow]")
            if install_ollama():
                DriftUI.show_success("Ollama installed")
            else:
                DriftUI.show_error(
                    "Auto-install failed. Install manually: https://ollama.com"
                )
        else:
            DriftUI.show_error("Ollama is not installed")
            console.print("  Install from https://ollama.com")
            console.print(
                "  [dim]Or set auto_install_ollama: true in ~/.drift/config.json[/dim]"
            )

    # ── Ollama server ──
    if is_ollama_installed():
        if is_ollama_running(config.ollama_url):
            DriftUI.show_success("Ollama is running")
        else:
            all_good = False
            if config.auto_start_ollama:
                console.print("[yellow]  Ollama not running — starting...[/yellow]")
                if start_ollama(config.ollama_url):
                    DriftUI.show_success("Ollama started")
                else:
                    DriftUI.show_error("Failed to start Ollama. Try: ollama serve")
            else:
                DriftUI.show_warning("Ollama is not running")
                console.print("  Start with: ollama serve")
                console.print(
                    "  [dim]Or set auto_start_ollama: true in ~/.drift/config.json[/dim]"
                )

    # ── Model ──
    console.print()
    console.print("[bold]Checking model...[/bold]")
    console.print(f"  Configured: {model}")
    if is_ollama_running(config.ollama_url):
        if is_model_available(model, config.ollama_url):
            DriftUI.show_success(f"Model {model} is ready")
        else:
            all_good = False
            if config.auto_pull_model:
                console.print(
                    f"[yellow]  Model {model} not found — pulling...[/yellow]"
                )
                if pull_model(model, config.ollama_url):
                    DriftUI.show_success(f"Model {model} pulled")
                else:
                    DriftUI.show_error(
                        f"Failed to pull {model}. Try: ollama pull {model}"
                    )
            else:
                DriftUI.show_warning(f"Model {model} is not available")
                console.print(f"  Pull with: ollama pull {model}")
                console.print(
                    "  [dim]Or set auto_pull_model: true in ~/.drift/config.json[/dim]"
                )
    elif is_ollama_installed():
        DriftUI.show_warning("Cannot check model — Ollama is not running")

    # ── Auto-setup settings ──
    console.print()
    console.print("[bold]Auto-setup settings...[/bold]")
    console.print(
        f"  auto_install_ollama: {'[green]ON[/green]' if config.auto_install_ollama else '[red]OFF[/red]'}"
    )
    console.print(
        f"  auto_start_ollama:   {'[green]ON[/green]' if config.auto_start_ollama else '[red]OFF[/red]'}"
    )
    console.print(
        f"  auto_pull_model:     {'[green]ON[/green]' if config.auto_pull_model else '[red]OFF[/red]'}"
    )

    # Check Drift directory
    console.print()
    console.print("[bold]Checking Drift directory...[/bold]")
    drift_dir = Path.home() / ".drift"
    if drift_dir.exists():
        DriftUI.show_success(f"Drift directory exists: {drift_dir}")
        hist_file = drift_dir / "history.jsonl"
        if hist_file.exists():
            console.print(f"  History file: {hist_file}")
        snapshots_dir = drift_dir / "snapshots"
        if snapshots_dir.exists():
            snapshot_count = len(list(snapshots_dir.iterdir()))
            console.print(f"  Snapshots: {snapshot_count}")
    else:
        DriftUI.show_warning(f"Drift directory not found: {drift_dir}")

    # Check ZSH integration
    console.print()
    console.print("[bold]Checking ZSH integration...[/bold]")
    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        content = zshrc.read_text()
        if "drift.zsh" in content:
            DriftUI.show_success("drift.zsh is sourced in ~/.zshrc")
        else:
            DriftUI.show_warning("drift.zsh not found in ~/.zshrc")
            console.print("  Run the installer to set it up")
    else:
        DriftUI.show_warning("~/.zshrc not found")

    console.print()
    console.print("[dim]All checks complete[/dim]")


@app.command()
def version():
    """Show Drift CLI version."""
    from drift_cli import __version__

    console.print(f"Drift CLI v{__version__}")


if __name__ == "__main__":
    app()
