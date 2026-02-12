"""First-run setup wizard for Drift CLI."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from drift_cli.core.auto_setup import ensure_ollama_ready
from drift_cli.core.config import ConfigManager, DriftConfig

console = Console()

WELCOME_ART = """[bold cyan]
     ╔══════════════════════════════════════╗
     ║         Welcome to Drift CLI         ║
     ║   Terminal AI assistant for humans   ║
     ╚══════════════════════════════════════╝[/bold cyan]"""

DRIFT_DIR = Path.home() / ".drift"


def is_first_run() -> bool:
    """Check if this is the first time Drift is run."""
    return not DRIFT_DIR.exists()


def run_setup_wizard():
    """Run the interactive first-run setup wizard.

    Creates ~/.drift, saves default config, and optionally
    installs/starts Ollama and pulls the default model.
    """
    console.print(WELCOME_ART)
    console.print()
    console.print("  Drift turns natural language into shell commands")
    console.print("  with built-in safety checks and undo support.")
    console.print()
    console.print("[dim]  Powered by local LLMs via Ollama — your data stays on your machine.[/dim]")
    console.print()

    # Create config directory
    DRIFT_DIR.mkdir(parents=True, exist_ok=True)

    # Save default config
    cm = ConfigManager()
    config = DriftConfig()
    cm.save(config)
    console.print("[green]✓[/green] Config created at ~/.drift/config.json")

    # Offer to set up Ollama
    console.print()
    setup_now = Confirm.ask(
        "[bold]Set up Ollama now?[/bold] (install, start, pull model)",
        default=True,
    )

    if setup_now:
        console.print()
        ready = ensure_ollama_ready(
            model=config.model,
            base_url=config.ollama_url,
            auto_install=True,
            auto_start=True,
            auto_pull=True,
        )
        if ready:
            console.print()
            console.print("[bold green]✓ Setup complete — Drift is ready![/bold green]")
        else:
            console.print()
            console.print("[yellow]Setup incomplete. Run [bold]drift doctor[/bold] to retry.[/yellow]")
    else:
        console.print()
        console.print("[dim]Skipped. Run [bold]drift doctor[/bold] when you're ready.[/dim]")

    # Quick-start tips
    console.print()
    console.print(Panel(
        "[cyan]drift suggest[/cyan] [dim]\"list large files\"[/dim]     — get command suggestions\n"
        "[cyan]drift explain[/cyan] [dim]\"tar -xzf a.tar.gz\"[/dim]   — explain a command\n"
        "[cyan]drift find[/cyan] [dim]\"todo comments\"[/dim]           — smart file search\n"
        "[cyan]drift doctor[/cyan]                          — check system health\n"
        "[cyan]drift help[/cyan]                            — show all commands",
        title="[bold]Quick Start[/bold]",
        border_style="cyan",
    ))
    console.print()
