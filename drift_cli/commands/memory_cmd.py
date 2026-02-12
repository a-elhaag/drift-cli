"""Memory management CLI commands."""

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from drift_cli.core.history import HistoryManager
from drift_cli.core.memory import MemoryManager

console = Console()
memory_app = typer.Typer(help="Manage Drift's memory and learned preferences")


@memory_app.command("show")
def show_memory():
    """Show what Drift has learned about your preferences."""
    memory = MemoryManager()
    history_manager = HistoryManager()

    # Learn from history first
    history = history_manager.get_history(limit=100)
    if history:
        memory.learn_from_history(history)

    console.print("\n[bold cyan]🧠 Drift Memory - What I've Learned About You[/bold cyan]\n")

    # User Preferences
    prefs_table = Table(title="Your Preferences", box=box.ROUNDED)
    prefs_table.add_column("Aspect", style="cyan")
    prefs_table.add_column("Preference", style="green")

    prefs_table.add_row(
        "Risk Tolerance",
        "Comfortable with high-risk"
        if memory.preferences.comfortable_with_high_risk
        else "Prefers safer approaches",
    )
    prefs_table.add_row(
        "Dry-run Preference", "Enabled" if memory.preferences.prefers_dry_run else "Disabled"
    )
    prefs_table.add_row(
        "Explanation Style",
        "Verbose" if memory.preferences.prefers_verbose_explanations else "Concise",
    )

    console.print(prefs_table)
    console.print()

    # Favorite Tools
    if memory.preferences.favorite_tools:
        tools_table = Table(title="Your Favorite Tools", box=box.ROUNDED)
        tools_table.add_column("Rank", justify="right", style="cyan")
        tools_table.add_column("Tool", style="green")
        tools_table.add_column("Usage", style="yellow")

        for i, tool in enumerate(memory.preferences.favorite_tools[:10], 1):
            tools_table.add_row(str(i), tool, "⭐" * min(5, 6 - i))

        console.print(tools_table)
        console.print()

    # Avoided Patterns
    if memory.preferences.avoided_patterns:
        avoided_panel = Panel(
            "\n".join(f"• {pattern}" for pattern in memory.preferences.avoided_patterns),
            title="[yellow]Commands You Often Skip[/yellow]",
            border_style="yellow",
        )
        console.print(avoided_panel)
        console.print()

    # Common Sequences
    if memory.preferences.common_sequences:
        seq_table = Table(title="Your Common Workflows", box=box.ROUNDED)
        seq_table.add_column("Workflow", style="cyan")

        for sequence in memory.preferences.common_sequences[:5]:
            workflow = " → ".join(sequence)
            seq_table.add_row(workflow)

        console.print(seq_table)
        console.print()

    # Current Context
    context_table = Table(title="Current Context", box=box.ROUNDED)
    context_table.add_column("Info", style="cyan")
    context_table.add_column("Value", style="green")

    context_table.add_row("Directory", memory.context.current_directory)

    if memory.context.current_git_repo:
        context_table.add_row("Git Repo", memory.context.current_git_repo)

    if memory.context.detected_project_type:
        context_table.add_row("Project Type", memory.context.detected_project_type)

    if memory.context.recent_queries:
        recent = ", ".join(memory.context.recent_queries[-3:])
        context_table.add_row("Recent Queries", recent)

    console.print(context_table)
    console.print()

    # Learning Tips
    tips = memory.detect_learning_opportunities(history)
    if tips:
        tips_panel = Panel(
            "\n\n".join(tips), title="[cyan]💡 Tips for You[/cyan]", border_style="cyan"
        )
        console.print(tips_panel)
        console.print()

    # Success Rates
    success_rates = memory.analyze_command_success_rate(history)
    if success_rates:
        success_table = Table(title="Command Success Rates", box=box.ROUNDED)
        success_table.add_column("Tool", style="cyan")
        success_table.add_column("Success Rate", justify="right")
        success_table.add_column("", justify="left")

        for tool, rate in sorted(success_rates.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = f"{rate * 100:.0f}%"
            bar = "█" * int(rate * 10)
            success_table.add_row(tool, percentage, bar)

        console.print(success_table)
        console.print()


@memory_app.command("stats")
def show_stats():
    """Show statistics about your Drift usage."""
    history_manager = HistoryManager()
    history = history_manager.get_history(limit=500)

    if not history:
        console.print("[yellow]No history found yet. Start using Drift![/yellow]")
        return

    console.print("\n[bold cyan]📊 Drift Usage Statistics[/bold cyan]\n")

    # Overall stats
    total_queries = len(history)
    executed = sum(1 for entry in history if entry.executed)
    successful = sum(1 for entry in history if entry.executed and entry.exit_code == 0)

    stats_table = Table(title="Overall Usage", box=box.ROUNDED)
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", justify="right", style="green")

    stats_table.add_row("Total Queries", str(total_queries))
    stats_table.add_row("Commands Executed", str(executed))
    stats_table.add_row("Successful", str(successful))

    if executed > 0:
        exec_rate = (executed / total_queries) * 100
        stats_table.add_row("Execution Rate", f"{exec_rate:.1f}%")

    if executed > 0:
        success_rate = (successful / executed) * 100
        stats_table.add_row("Success Rate", f"{success_rate:.1f}%")

    console.print(stats_table)
    console.print()

    # Risk distribution
    risk_counts = {"low": 0, "medium": 0, "high": 0}
    for entry in history:
        if entry.executed:
            risk_counts[entry.plan.risk.value] += 1

    if any(risk_counts.values()):
        risk_table = Table(title="Risk Distribution (Executed)", box=box.ROUNDED)
        risk_table.add_column("Risk Level", style="cyan")
        risk_table.add_column("Count", justify="right")
        risk_table.add_column("Percentage", justify="right")

        total_executed = sum(risk_counts.values())
        for risk_level, count in risk_counts.items():
            if count > 0:
                pct = (count / total_executed) * 100
                risk_table.add_row(risk_level.upper(), str(count), f"{pct:.1f}%")

        console.print(risk_table)
        console.print()


@memory_app.command("reset")
def reset_memory(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Reset all learned preferences (keeps history)."""
    if not confirm:
        console.print("[yellow]This will reset all learned preferences.[/yellow]")
        console.print("[yellow]Your command history will NOT be deleted.[/yellow]\n")

        response = typer.prompt("Are you sure? (y/N)", default="N")
        if response.lower() != "y":
            console.print("[cyan]Cancelled.[/cyan]")
            raise typer.Exit(0)

    memory = MemoryManager()
    memory.reset()

    console.print("[green]✓ Memory reset successfully![/green]")
    console.print("[cyan]Drift will learn your preferences as you use it.[/cyan]")


@memory_app.command("insights")
def show_insights():
    """Show personalized insights and suggestions."""
    memory = MemoryManager()
    history_manager = HistoryManager()

    history = history_manager.get_history(limit=100)
    if not history:
        console.print("[yellow]No history found yet. Start using Drift![/yellow]")
        return

    memory.learn_from_history(history)

    console.print("\n[bold cyan]🔍 Personalized Insights[/bold cyan]\n")

    # Context that will be sent to LLM
    context = memory.get_personalized_prompt_context()
    context_panel = Panel(context, title="[cyan]Context Sent to AI[/cyan]", border_style="cyan")
    console.print(context_panel)
    console.print()

    # Pattern-based suggestions
    suggestions = memory.suggest_based_on_patterns("general workflow")
    if suggestions:
        sugg_panel = Panel(
            "\n\n".join(f"• {s}" for s in suggestions),
            title="[green]Smart Suggestions[/green]",
            border_style="green",
        )
        console.print(sugg_panel)
        console.print()

    # Tips
    tips = memory.detect_learning_opportunities(history)
    if tips:
        tips_panel = Panel(
            "\n\n".join(tips),
            title="[yellow]💡 Opportunities to Improve[/yellow]",
            border_style="yellow",
        )
        console.print(tips_panel)
        console.print()


@memory_app.command("export")
def export_memory(output: str = typer.Argument(..., help="Output file path (JSON format)")):
    """Export learned preferences to a file."""
    import json
    from datetime import datetime
    from pathlib import Path

    memory = MemoryManager()
    output_path = Path(output).expanduser()

    # Prepare export data
    export_data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "current_project": memory.current_project,
        "preferences": {
            "comfortable_with_high_risk": memory.preferences.comfortable_with_high_risk,
            "prefers_dry_run": memory.preferences.prefers_dry_run,
            "prefers_verbose_explanations": memory.preferences.prefers_verbose_explanations,
            "favorite_tools": list(memory.preferences.favorite_tools),  # Convert to list
            "avoided_patterns": list(memory.preferences.avoided_patterns),
            "common_sequences": [list(seq) for seq in memory.preferences.common_sequences],
        },
    }

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        console.print(f"[green]✓ Memory exported to: {output_path}[/green]")
        if memory.current_project:
            console.print(f"[cyan]Project: {memory.current_project}[/cyan]")
        console.print(f"[cyan]File size: {output_path.stat().st_size} bytes[/cyan]")
    except Exception as e:
        console.print(f"[red]✗ Export failed: {e}[/red]")
        raise typer.Exit(1)


@memory_app.command("projects")
def list_projects():
    """List all projects with learned preferences."""
    import json

    memory = MemoryManager()
    projects_dir = memory.projects_dir

    if not projects_dir.exists():
        console.print("[yellow]No project-specific memories found.[/yellow]")
        return

    project_files = list(projects_dir.glob("*.json"))

    if not project_files:
        console.print("[yellow]No project-specific memories found.[/yellow]")
        return

    console.print("\n[bold cyan]📁 Projects with Learned Preferences[/bold cyan]\n")

    table = Table(title=f"{len(project_files)} Projects", box=box.ROUNDED)
    table.add_column("Project", style="cyan")
    table.add_column("Last Updated", style="yellow")
    table.add_column("Tools", style="green")
    table.add_column("Patterns", style="magenta")

    for project_file in sorted(project_files):
        try:
            with open(project_file) as f:
                data = json.load(f)

            project_name = data.get("project", project_file.stem)
            last_updated = data.get("last_updated", "Unknown")
            if last_updated != "Unknown":
                # Format timestamp
                from datetime import datetime

                dt = datetime.fromisoformat(last_updated)
                last_updated = dt.strftime("%Y-%m-%d %H:%M")

            prefs = data.get("preferences", {})
            tools_count = len(prefs.get("favorite_tools", []))
            patterns_count = len(prefs.get("avoided_patterns", []))

            table.add_row(project_name, last_updated, str(tools_count), str(patterns_count))
        except Exception:
            continue

    console.print(table)
    console.print("\n[dim]Use 'drift memory show' to see current project preferences[/dim]")


@memory_app.command("import")
def import_memory(
    input_file: str = typer.Argument(..., help="Input file path (JSON format)"),
    merge: bool = typer.Option(
        False,
        "--merge",
        "-m",
        help="Merge with existing preferences instead of replacing",
    ),
):
    """Import learned preferences from a file."""
    import json
    from pathlib import Path

    memory = MemoryManager()
    input_path = Path(input_file).expanduser()

    if not input_path.exists():
        console.print(f"[red]✗ File not found: {input_path}[/red]")
        raise typer.Exit(1)

    try:
        with open(input_path) as f:
            import_data = json.load(f)

        # Validate version
        if import_data.get("version") != "1.0":
            console.print("[yellow]⚠ Warning: Version mismatch. Proceeding anyway...[/yellow]")

        prefs_data = import_data["preferences"]

        if merge:
            # Merge with existing preferences
            console.print("[cyan]Merging preferences...[/cyan]")

            # Merge favorite tools (combine lists, keep unique)
            existing_tools = set(memory.preferences.favorite_tools)
            imported_tools = set(prefs_data["favorite_tools"])
            memory.preferences.favorite_tools = list(existing_tools | imported_tools)

            # Merge avoided patterns (union)
            memory.preferences.avoided_patterns = list(
                set(memory.preferences.avoided_patterns) | set(prefs_data["avoided_patterns"])
            )

            # Merge sequences (union)
            existing_seqs = set(tuple(s) for s in memory.preferences.common_sequences)
            imported_seqs = set(tuple(s) for s in prefs_data["common_sequences"])
            memory.preferences.common_sequences = [list(s) for s in (existing_seqs | imported_seqs)]

            # For boolean prefs, use OR logic (if either is true, keep true)
            memory.preferences.comfortable_with_high_risk = (
                memory.preferences.comfortable_with_high_risk
                or prefs_data["comfortable_with_high_risk"]
            )
        else:
            # Replace entirely
            console.print("[cyan]Replacing preferences...[/cyan]")
            memory.preferences.comfortable_with_high_risk = prefs_data["comfortable_with_high_risk"]
            memory.preferences.prefers_dry_run = prefs_data["prefers_dry_run"]
            memory.preferences.prefers_verbose_explanations = prefs_data[
                "prefers_verbose_explanations"
            ]
            memory.preferences.favorite_tools = list(prefs_data["favorite_tools"])
            memory.preferences.avoided_patterns = prefs_data["avoided_patterns"]
            memory.preferences.common_sequences = prefs_data["common_sequences"]

        # Save updated preferences
        memory._save_preferences()

        console.print("[green]✓ Memory imported successfully![/green]")
        console.print(
            f"[cyan]Imported {len(prefs_data['favorite_tools'])} tools, "
            f"{len(prefs_data['avoided_patterns'])} patterns[/cyan]"
        )
    except Exception as e:
        console.print(f"[red]✗ Import failed: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    memory_app()
