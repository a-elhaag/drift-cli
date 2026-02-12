"""AI-powered suggestion, search, and explanation commands."""

import os

import typer
from rich.console import Console

from drift_cli.core.auto_setup import ensure_ollama_ready
from drift_cli.core.config import ConfigManager
from drift_cli.core.executor import Executor
from drift_cli.core.history import HistoryManager
from drift_cli.core.memory import MemoryManager
from drift_cli.core.ollama import OllamaClient
from drift_cli.core.safety import SafetyChecker
from drift_cli.core.slash_commands import SlashCommandHandler
from drift_cli.ui.display import DriftUI

console = Console()

suggest_app = typer.Typer()


def _get_config():
    return ConfigManager()


def _get_ollama_client() -> OllamaClient:
    config = _get_config().load()
    model = os.getenv("DRIFT_MODEL", config.model)
    return OllamaClient(base_url=config.ollama_url, model=model)


def _check_ollama():
    """Ensure Ollama is ready, using auto-setup config settings."""
    config = _get_config().load()
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


@suggest_app.command("suggest")
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
    from pathlib import Path

    # Auto-cleanup old snapshots silently
    try:
        snapshots_dir = Path.home() / ".drift" / "snapshots"
        if snapshots_dir.exists():
            count = sum(1 for d in snapshots_dir.iterdir() if d.is_dir())
            if count > 100:
                HistoryManager().cleanup_old_snapshots(keep=50, max_age_days=30)
    except Exception:
        pass

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

    _check_ollama()

    client = _get_ollama_client()
    executor = Executor()
    history = HistoryManager()

    try:
        context = executor.get_context()

        if memory:
            context = memory.enhance_prompt_with_context(context)

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


@suggest_app.command("find")
def find(query: str = typer.Argument(..., help="What to find")):
    """Smart file and content search."""
    find_query = f"Find: {query}. Use safe read-only commands like 'find', 'rg', 'grep', 'fd', or 'ls'. Do not modify any files."
    suggest(query=find_query, execute=False, dry_run=False, verbose=False)


@suggest_app.command("explain")
def explain(command: str = typer.Argument(..., help="Command to explain")):
    """Explain what a shell command does."""
    _check_ollama()
    client = _get_ollama_client()
    try:
        explanation = client.explain_command(command)
        console.print()
        console.print(explanation)
    except ValueError as e:
        DriftUI.show_error(str(e))
        raise typer.Exit(1)
    finally:
        client.close()
