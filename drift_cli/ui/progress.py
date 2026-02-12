"""Progress and status utilities for Drift CLI."""

import sys
import time
from typing import Optional

from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

console = Console()


class ProgressSpinner:
    """Displays a progress spinner during long operations."""

    def __init__(self, message: str = "Processing..."):
        self.message = message
        self.live: Optional[Live] = None
        self.spinner = Spinner("dots", text=message)

    def start(self):
        """Start the spinner."""
        try:
            self.live = Live(self.spinner, console=console, refresh_per_second=10)
            self.live.start()
        except Exception:
            # Fallback for non-TTY environments
            console.print(f"[cyan]{self.message}[/cyan]", end="", flush=True)

    def stop(self, success: bool = True):
        """Stop the spinner."""
        if self.live:
            try:
                self.live.stop()
            except Exception:
                pass
        else:
            # For non-TTY, add newline
            if not success:
                console.print(" [red]✗[/red]")
            else:
                console.print(" [green]✓[/green]")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(success=exc_type is None)


def show_timeout_warning(seconds: int):
    """Show warning about long operation."""
    console.print(
        f"[yellow]⏱  This may take {seconds} seconds or longer...[/yellow]"
    )
