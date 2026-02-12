"""Progress and status utilities for Drift CLI."""

from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

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
            console.print(f"[cyan]{self.message}[/cyan]", end="", flush=True)

    def stop(self, success: bool = True):
        """Stop the spinner."""
        if self.live:
            try:
                self.live.stop()
            except Exception:
                pass
        else:
            if not success:
                console.print(" [red]✗[/red]")
            else:
                console.print(" [green]✓[/green]")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop(success=exc_type is None)
