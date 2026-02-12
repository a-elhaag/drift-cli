"""Rich-based UI components for Drift CLI."""

from typing import List, Optional, TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from drift_cli.models import Command, Plan, RiskLevel

if TYPE_CHECKING:
    from drift_cli.core.memory import MemoryManager

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
    def show_plan(cls, plan: Plan, query: str):
        """Display a plan with rich formatting."""
        # Header
        console.print()
        console.print(f"[bold cyan]Query:[/bold cyan] {query}")
        console.print()

        # Risk badge
        risk_color = cls.RISK_COLORS[plan.risk]
        risk_emoji = cls.RISK_EMOJI[plan.risk]
        risk_badge = f"[{risk_color}]{risk_emoji} {plan.risk.value.upper()}[/{risk_color}]"

        # Summary panel
        summary_content = f"{plan.summary}\n\n{risk_badge}"
        console.print(
            Panel(
                summary_content,
                title="[bold]Plan Summary[/bold]",
                border_style="cyan",
            )
        )

        # Commands table
        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("#", style="dim", width=3)
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")

        for idx, cmd in enumerate(plan.commands, 1):
            table.add_row(str(idx), cmd.command, cmd.description)

        console.print(table)
        console.print()

        # Explanation
        console.print(Panel(plan.explanation, title="[bold]Explanation[/bold]", border_style="blue"))

        # Affected files (if any)
        if plan.affected_files:
            files_text = "\n".join(f"  • {f}" for f in plan.affected_files)
            console.print(
                Panel(
                    files_text,
                    title="[bold]Affected Files[/bold]",
                    border_style="yellow",
                )
            )

        console.print()
    
    @classmethod
    def show_memory_suggestions(cls, memory: Optional["MemoryManager"], query: str):
        """Show memory-based suggestions and patterns."""
        if not memory:
            return
        
        # Get pattern-based suggestions
        suggestions = memory.suggest_based_on_patterns(query)
        
        if suggestions:
            console.print()
            suggestions_text = "\n".join(f"• {s}" for s in suggestions)
            console.print(
                Panel(
                    suggestions_text,
                    title="[cyan]💡 Smart Suggestions (based on your patterns)[/cyan]",
                    border_style="cyan",
                    style="dim"
                )
            )
        
        # Show project context if available
        if memory.context.detected_project_type:
            project_badge = f"[dim]📦 {memory.context.detected_project_type} project detected[/dim]"
            console.print(project_badge)

    @classmethod
    def show_commands_preview(cls, commands: List[Command]):
        """Show a preview of commands to be executed."""
        console.print("[bold]Preview of commands to execute:[/bold]")
        console.print()

        for idx, cmd in enumerate(commands, 1):
            # Show dry-run if available, otherwise the actual command
            preview_cmd = cmd.dry_run or cmd.command
            syntax = Syntax(preview_cmd, "bash", theme="monokai", line_numbers=False)
            console.print(f"[dim]{idx}.[/dim] {cmd.description}")
            console.print(syntax)
            console.print()

    @classmethod
    def confirm_execution(cls, risk: RiskLevel) -> bool:
        """Ask user to confirm execution."""
        if risk == RiskLevel.HIGH:
            console.print()
            console.print(
                Panel(
                    "[bold red]⚠️  DANGEROUS OPERATION[/bold red]\n\n"
                    "This command has been flagged as HIGH RISK.\n"
                    "It may cause significant changes to your system.\n\n"
                    "[yellow]Review the commands above carefully before proceeding.[/yellow]",
                    title="[bold red]⚠️  HIGH RISK[/bold red]",
                    border_style="red",
                    style="bold",
                )
            )
            console.print()
            # Require explicit typing for high risk
            response = Prompt.ask(
                "[bold red]Type 'YES' to proceed with HIGH RISK operation[/bold red]",
                default="N",
            )
            return response.upper() == "YES"
        else:
            console.print()
            return Confirm.ask("[bold]Proceed with execution?[/bold]", default=False)

    @classmethod
    def show_execution_result(cls, exit_code: int, output: str):
        """Display execution results."""
        if exit_code == 0:
            console.print("[bold green]✓ Execution completed successfully[/bold green]")
        else:
            console.print(f"[bold red]✗ Execution failed (exit code: {exit_code})[/bold red]")

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
        console.print(f"[bold cyan]ℹ[/bold cyan] {message}")

    @classmethod
    def ask_clarification(cls, questions: List) -> dict:
        """Ask clarification questions and return answers."""
        console.print("[bold yellow]Need clarification:[/bold yellow]")
        console.print()

        answers = {}
        for idx, q in enumerate(questions):
            if q.options:
                console.print(f"[bold]{q.question}[/bold]")
                for i, option in enumerate(q.options, 1):
                    console.print(f"  {i}. {option}")
                answer = Prompt.ask("Your choice", choices=[str(i) for i in range(1, len(q.options) + 1)])
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
        table.add_column("Status", style="green", width=15)
        table.add_column("Risk", style="yellow", width=10)

        for entry in entries:
            status = "✓ Executed" if entry.executed else "○ Planned"
            status_style = "green" if entry.executed else "dim"

            # Format timestamp
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(entry.timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                time_str = entry.timestamp[:19]

            table.add_row(
                time_str,
                entry.query[:40] + "..." if len(entry.query) > 40 else entry.query,
                Text(status, style=status_style),
                entry.plan.risk.value,
            )

        console.print(table)
