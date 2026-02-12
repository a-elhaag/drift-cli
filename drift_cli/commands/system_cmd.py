"""System management commands: doctor, config, setup, update, uninstall, version."""

import os
import sys
from pathlib import Path

import typer
from rich.console import Console

from drift_cli.core.auto_setup import ensure_ollama_ready
from drift_cli.core.config import ConfigManager, DriftConfig
from drift_cli.core.first_run import run_setup_wizard
from drift_cli.ui.display import DriftUI

console = Console()

system_app = typer.Typer()


def _get_config() -> ConfigManager:
    return ConfigManager()


@system_app.command("doctor")
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

    config = _get_config().load()
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


@system_app.command("config")
def config():
    """View and change Drift settings interactively."""
    from rich.prompt import Confirm, Prompt

    cm = _get_config()
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


@system_app.command("setup")
def setup():
    """Re-run the first-time setup wizard."""
    run_setup_wizard()


@system_app.command("update")
def update():
    """Update Drift CLI to the latest version."""
    import subprocess

    repo_dir = Path(__file__).resolve().parent.parent.parent

    git_dir = repo_dir / ".git"
    if not git_dir.exists():
        console.print(
            "[red]✗ Cannot auto-update: Drift was not installed from a git clone.[/red]"
        )
        console.print(
            "  [dim]Reinstall with:[/dim]  git clone https://github.com/a-elhaag/drift-cli.git && cd drift-cli && pip install -e ."
        )
        raise typer.Exit(1)

    console.print("[cyan]🔄 Checking for updates...[/cyan]")

    try:
        subprocess.run(
            ["git", "fetch", "--quiet"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        behind = subprocess.run(
            ["git", "rev-list", "--count", "HEAD..@{u}"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )

        commits_behind = int(behind.stdout.strip() or "0")

        if commits_behind == 0:
            console.print("[green]✓ Drift CLI is already up to date.[/green]")
            return

        console.print(
            f"[yellow]  {commits_behind} new commit{'s' if commits_behind != 1 else ''} available[/yellow]"
        )

        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            console.print(
                "[red]✗ Update failed (merge conflict or diverged branch).[/red]"
            )
            console.print(f"  [dim]{result.stderr.strip()}[/dim]")
            raise typer.Exit(1)

        pip_result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", ".", "--quiet"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if pip_result.returncode != 0:
            console.print("[yellow]⚠ Code updated but pip install had issues:[/yellow]")
            console.print(f"  [dim]{pip_result.stderr.strip()}[/dim]")
        else:
            from drift_cli import __version__

            console.print(f"[green]✓ Updated to Drift CLI v{__version__}[/green]")

    except subprocess.TimeoutExpired:
        console.print("[red]✗ Update timed out. Check your network connection.[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]✗ Update failed: {e}[/red]")
        raise typer.Exit(1)


@system_app.command("uninstall")
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

    drift_dir = Path.home() / ".drift"
    if drift_dir.exists():
        shutil.rmtree(drift_dir)
        DriftUI.show_success("Removed ~/.drift")
    else:
        console.print("[dim]  ~/.drift not found (skipped)[/dim]")

    from drift_cli.core.auto_setup import is_ollama_installed

    if is_ollama_installed():
        console.print()
        if typer.confirm("Also uninstall Ollama?", default=False):
            import platform

            system = platform.system().lower()

            try:
                if system == "darwin":
                    subprocess.run(["pkill", "-f", "Ollama"], capture_output=True)
                    app_path = Path("/Applications/Ollama.app")
                    if app_path.exists():
                        shutil.rmtree(app_path)
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

    console.print()
    console.print("[yellow]To finish, run:[/yellow]")
    console.print("  [cyan]pip uninstall drift-cli[/cyan]")
    console.print()


@system_app.command("version")
def version():
    """Show Drift CLI version."""
    from drift_cli import __version__

    console.print(f"Drift CLI v{__version__}")
