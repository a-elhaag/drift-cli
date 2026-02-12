"""Auto-setup utilities for Ollama installation, model pulling, and server management."""

import platform
import shutil
import subprocess
import time
from typing import Optional

import httpx
from rich.console import Console

console = Console()


def is_ollama_installed() -> bool:
    """Check if the Ollama binary is available on the system."""
    return shutil.which("ollama") is not None


def is_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """Check if the Ollama server is running and reachable."""
    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        return resp.status_code == 200
    except Exception:
        return False


def is_model_available(model: str, base_url: str = "http://localhost:11434") -> bool:
    """Check if a specific model is pulled and available locally."""
    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        if resp.status_code != 200:
            return False
        data = resp.json()
        available = [m.get("name", "") for m in data.get("models", [])]
        # Match both "model:tag" and just "model" (Ollama sometimes includes :latest)
        for name in available:
            if (
                name == model
                or name.startswith(f"{model}:")
                or model.startswith(f"{name.split(':')[0]}")
            ):
                return True
            # Also check without tag
            if ":" in model:
                base, tag = model.rsplit(":", 1)
                if name == model or name == f"{base}:{tag}":
                    return True
        return False
    except Exception:
        return False


def install_ollama() -> bool:
    """Install Ollama automatically.

    On macOS: Uses Homebrew if available, otherwise downloads from ollama.com.
    On Linux: Uses the official install script.

    Returns:
        True if installation succeeded.
    """
    system = platform.system().lower()

    console.print("[cyan]📦 Installing Ollama...[/cyan]")

    try:
        if system == "darwin":
            # macOS — try brew first, then direct download
            if shutil.which("brew"):
                console.print("[dim]  Using Homebrew...[/dim]")
                result = subprocess.run(
                    ["brew", "install", "ollama"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                if result.returncode == 0:
                    console.print("[green]  ✓ Ollama installed via Homebrew[/green]")
                    return True

            # Fallback: download the macOS app
            console.print("[dim]  Downloading from ollama.com...[/dim]")
            result = subprocess.run(
                [
                    "curl",
                    "-fsSL",
                    "-o",
                    "/tmp/Ollama.dmg",
                    "https://ollama.com/download/Ollama-darwin.zip",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                # Try to unzip and install
                subprocess.run(
                    ["unzip", "-o", "/tmp/Ollama-darwin.zip", "-d", "/Applications/"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                if shutil.which("ollama") or (
                    subprocess.run(
                        ["test", "-d", "/Applications/Ollama.app"], capture_output=True
                    ).returncode
                    == 0
                ):
                    console.print("[green]  ✓ Ollama installed[/green]")
                    return True

            console.print(
                "[yellow]  ⚠ Auto-install failed. Install manually from https://ollama.com[/yellow]"
            )
            return False

        elif system == "linux":
            console.print("[dim]  Using official install script...[/dim]")
            result = subprocess.run(
                ["sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode == 0:
                console.print("[green]  ✓ Ollama installed[/green]")
                return True
            console.print(
                "[yellow]  ⚠ Auto-install failed. Install manually from https://ollama.com[/yellow]"
            )
            return False

        else:
            console.print(
                f"[yellow]  ⚠ Auto-install not supported on {system}. Install from https://ollama.com[/yellow]"
            )
            return False

    except subprocess.TimeoutExpired:
        console.print(
            "[yellow]  ⚠ Installation timed out. Install manually from https://ollama.com[/yellow]"
        )
        return False
    except Exception as e:
        console.print(f"[yellow]  ⚠ Installation failed: {e}[/yellow]")
        return False


def start_ollama(base_url: str = "http://localhost:11434", timeout: int = 15) -> bool:
    """Start the Ollama server.

    On macOS: Tries `open -a Ollama`, then falls back to `ollama serve`.
    On Linux: Starts `ollama serve` in the background.

    Args:
        base_url: The URL to check for Ollama availability.
        timeout: Seconds to wait for server to become ready.

    Returns:
        True if Ollama is running after the attempt.
    """
    system = platform.system().lower()

    console.print("[cyan]🚀 Starting Ollama...[/cyan]")

    try:
        if system == "darwin":
            # macOS — try opening the app first (handles the service)
            app_exists = (
                subprocess.run(
                    ["test", "-d", "/Applications/Ollama.app"],
                    capture_output=True,
                ).returncode
                == 0
            )

            if app_exists:
                subprocess.Popen(
                    ["open", "-a", "Ollama"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                # No app bundle, start serve in background
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        else:
            # Linux / other — start serve in background
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # Wait for it to become ready
        for i in range(timeout):
            time.sleep(1)
            if is_ollama_running(base_url):
                console.print("[green]  ✓ Ollama is running[/green]")
                return True

        console.print(
            "[yellow]  ⚠ Ollama started but not responding yet. Try again in a moment.[/yellow]"
        )
        return False

    except FileNotFoundError:
        console.print("[yellow]  ⚠ Ollama binary not found. Install it first.[/yellow]")
        return False
    except Exception as e:
        console.print(f"[yellow]  ⚠ Failed to start Ollama: {e}[/yellow]")
        return False


def pull_model(model: str, base_url: str = "http://localhost:11434") -> bool:
    """Pull a model using the Ollama CLI.

    Args:
        model: Model name (e.g. "qwen2.5-coder:1.5b").
        base_url: Ollama server URL (unused, pulls via CLI).

    Returns:
        True if the model was pulled successfully.
    """
    console.print(
        f"[cyan]📥 Pulling model [bold]{model}[/bold]... (this may take a few minutes)[/cyan]"
    )

    try:
        result = subprocess.run(
            ["ollama", "pull", model],
            timeout=600,  # 10 minute timeout for large models
        )
        if result.returncode == 0:
            console.print(f"[green]  ✓ Model {model} is ready[/green]")
            return True
        console.print(f"[yellow]  ⚠ Failed to pull model {model}[/yellow]")
        return False

    except subprocess.TimeoutExpired:
        console.print(
            f"[yellow]  ⚠ Model pull timed out. Run manually: ollama pull {model}[/yellow]"
        )
        return False
    except FileNotFoundError:
        console.print("[yellow]  ⚠ Ollama binary not found. Install it first.[/yellow]")
        return False
    except Exception as e:
        console.print(f"[yellow]  ⚠ Failed to pull model: {e}[/yellow]")
        return False


def ensure_ollama_ready(
    model: str,
    base_url: str = "http://localhost:11434",
    auto_install: bool = True,
    auto_start: bool = True,
    auto_pull: bool = True,
) -> bool:
    """Ensure Ollama is installed, running, and has the required model.

    This is the main entry point. It checks each prerequisite in order
    and attempts to fix missing ones based on the auto_* flags.

    Args:
        model: Required model name.
        base_url: Ollama server URL.
        auto_install: Automatically install Ollama if not found.
        auto_start: Automatically start Ollama if not running.
        auto_pull: Automatically pull the model if not available.

    Returns:
        True if Ollama is fully ready (installed, running, model available).
    """
    # Step 1: Is Ollama installed?
    if not is_ollama_installed():
        if auto_install:
            if not install_ollama():
                return False
            # Re-check after install
            if not is_ollama_installed():
                console.print("[red]✗ Ollama installation could not be verified[/red]")
                return False
        else:
            console.print("[red]✗ Ollama is not installed[/red]")
            console.print(
                "  Install from https://ollama.com or enable auto_install_ollama in config"
            )
            return False

    # Step 2: Is Ollama running?
    if not is_ollama_running(base_url):
        if auto_start:
            if not start_ollama(base_url):
                return False
        else:
            console.print("[red]✗ Ollama is not running[/red]")
            console.print("  Start with: ollama serve")
            console.print("  Or enable auto_start_ollama in config")
            return False

    # Step 3: Is the model available?
    if not is_model_available(model, base_url):
        if auto_pull:
            if not pull_model(model, base_url):
                return False
            # Verify after pull
            if not is_model_available(model, base_url):
                console.print(
                    f"[red]✗ Model {model} still not available after pull[/red]"
                )
                return False
        else:
            console.print(f"[red]✗ Model {model} is not available[/red]")
            console.print(f"  Pull it with: ollama pull {model}")
            console.print("  Or enable auto_pull_model in config")
            return False

    return True
