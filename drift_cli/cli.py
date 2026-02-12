"""Main CLI application — app setup, argv preprocessing, and entry point."""

import sys

import typer
from rich.console import Console
from rich.panel import Panel

from drift_cli.commands.history_cmd import history_app
from drift_cli.commands.memory_cmd import memory_app
from drift_cli.commands.suggest_cmd import suggest_app
from drift_cli.commands.system_cmd import system_app
from drift_cli.core.first_run import is_first_run, run_setup_wizard

# ---------------------------------------------------------------------------
# Known subcommands for argv preprocessing
# ---------------------------------------------------------------------------
_SUBCOMMANDS = {
    "suggest",
    "find",
    "explain",
    "history",
    "again",
    "undo",
    "cleanup",
    "doctor",
    "config",
    "uninstall",
    "update",
    "version",
    "setup",
    "memory",
}

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

    first = args[0]

    if not first.startswith("-") and first not in _SUBCOMMANDS:
        query = " ".join(args)
        sys.argv = [sys.argv[0], "suggest", query]
        return

    if first in _QUERY_SUBCOMMANDS and len(args) > 1:
        options = [a for a in args[1:] if a.startswith("-")]
        positional = [a for a in args[1:] if not a.startswith("-")]
        if len(positional) > 1:
            query = " ".join(positional)
            sys.argv = [sys.argv[0], first] + options + [query]


# ---------------------------------------------------------------------------
# Typer app — register all command groups
# ---------------------------------------------------------------------------
app = typer.Typer(
    name="drift",
    help="Terminal-native, safety-first AI assistant",
    add_completion=False,
    invoke_without_command=True,
)

for _sub_app in (suggest_app, history_app, system_app):
    for cmd_info in _sub_app.registered_commands:
        app.registered_commands.append(cmd_info)

app.add_typer(memory_app, name="memory")

console = Console()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Drift — terminal-native, safety-first AI assistant."""
    if is_first_run():
        run_setup_wizard()
        if ctx.invoked_subcommand is None:
            raise typer.Exit(0)

    if ctx.invoked_subcommand is None:
        _show_help()
        raise typer.Exit(0)


# ---------------------------------------------------------------------------
# Rich help screen
# ---------------------------------------------------------------------------
def _show_help():
    """Show a rich help screen with all commands."""
    from drift_cli import __version__

    console.print(f"\n[bold cyan]Drift CLI[/bold cyan] [dim]v{__version__}[/dim]")
    console.print("[dim]Terminal-native, safety-first AI assistant[/dim]\n")

    console.print(
        Panel(
            "[cyan]drift[/cyan] [dim]list large files[/dim]     Quick shortcut (same as suggest)\n"
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
            "[cyan]drift update[/cyan]                 Update to latest version\n"
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
            "\n[dim]Usage: drift /git  or  drift suggest /commit[/dim]",
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main_entry():
    """Entry point that preprocesses argv, then runs the Typer app."""
    _preprocess_argv()
    app()


if __name__ == "__main__":
    main_entry()
