"""Rich-based UI components for Drift CLI."""

from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from drift_cli.models import Plan, RiskLevel

console = Console()


class DriftUI:
    """UI components for Drift CLI using Rich."""

    RISK_COLORS = {
        RiskLevel.LOW: "green",
        RiskLevel.MEDIUM: "yellow",
        RiskLevel.HIGH: "red",
    }

    RISK_EMOJI = {
        RiskLevel.LOW: "✓",
        RiskLevel.MEDIUM: "⚡",
        RiskLevel.HIGH: "⚠️",
    }

    @classmethod
    def show_plan(cls, plan: Plan, query: str, show_explanation: bool = False):
        """Display a plan with rich formatting."""
        console.print()

        # Risk badge
        risk_color = cls.RISK_COLORS[plan.risk]
        risk_emoji = cls.RISK_EMOJI[plan.risk]

        # Compact header: summary + risk on one line
        console.print(
            f"[bold]{plan.summary}[/bold]  "
            f"[{risk_color}]{risk_emoji} {plan.risk.value.upper()}[/{risk_color}]"
        )
        console.print()

        # Commands table
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("#", style="dim", width=3)
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")

        for idx, cmd in enumerate(plan.commands, 1):
            table.add_row(str(idx), cmd.command, cmd.description)

        console.print(table)

        # Explanation (only with --verbose)
        if show_explanation and plan.explanation:
            console.print()
            console.print(Panel(plan.explanation, title="[bold]Explanation[/bold]", border_style="blue"))

        # Affected files
        if plan.affected_files:
            files = ", ".join(plan.affected_files)
            console.print(f"\n[dim]Affects: {files}[/dim]")

        console.print()

    @classmethod
    def confirm_execution(cls, risk: RiskLevel) -> bool:
        """Ask user to confirm execution."""
        if risk == RiskLevel.HIGH:
            console.print(
                "[bold red]⚠️  HIGH RISK — review commands carefully[/bold red]"
            )
            response = Prompt.ask(
                "[red]Type 'YES' to proceed[/red]",
                default="N",
            )
            return response.upper() == "YES"
        else:
            return Confirm.ask("[bold]Execute?[/bold]", default=False)

    @classmethod
    def show_execution_result(cls, exit_code: int, output: str):
        """Display execution results."""
        if exit_code == 0:
            console.print("[bold green]✓ Done[/bold green]")
        else:
            console.print(f"[bold red]✗ Failed (exit code: {exit_code})[/bold red]")

        if output:
            console.print()
            console.print(Panel(output, title="[bold]Output[/bold]", border_style="white"))

    @classmethod
    def show_error(cls, message: str):
        """Display an error message."""
        console.print(f"[bold red]Error:[/bold red] {message}")

    @classmethod
    def show_warning(cls, message: str):
        """Display a warning message."""
        console.print(f"[bold yellow]Warning:[/bold yellow] {message}")

    @classmethod
    def show_success(cls, message: str):
        """Display a success message."""
        console.print(f"[bold green]✓[/bold green] {message}")

    @classmethod
    def show_info(cls, message: str):
        """Display an info message."""
        console.print(f"[cyan]ℹ[/cyan] {message}")

    @classmethod
    def ask_clarification(cls, questions: List) -> dict:
        """Ask clarification questions and return answers."""
        console.print("[bold yellow]Need clarification:[/bold yellow]\n")

        answers = {}
        for idx, q in enumerate(questions):
            if q.options:
                console.print(f"[bold]{q.question}[/bold]")
                for i, option in enumerate(q.options, 1):
                    console.print(f"  {i}. {option}")
                answer = Prompt.ask("Choice", choices=[str(i) for i in range(1, len(q.options) + 1)])
                answers[idx] = q.options[int(answer) - 1]
            else:
                answer = Prompt.ask(f"[bold]{q.question}[/bold]")
                answers[idx] = answer
            console.print()

        return answers

    @classmethod
    def show_history(cls, entries: List):
        """Display command history."""
        if not entries:
            console.print("[dim]No history yet.[/dim]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Time", style="cyan", width=20)
        table.add_column("Query", style="white", width=40)
        table.add_column("Status", style="green", width=10)
        table.add_column("Risk", style="yellow", width=8)

        for entry in entries:
            status = "✓" if entry.executed else "○"
            style = "green" if entry.executed else "dim"

            try:
                from datetime import datetime
                dt = datetime.fromisoformat(entry.timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                time_str = entry.timestamp[:16]

            query_text = entry.query[:40] + "…" if len(entry.query) > 40 else entry.query

            table.add_row(
                time_str,
                query_text,
                Text(status, style=style),
                entry.plan.risk.value,
            )

        console.print(table)
