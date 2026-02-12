"""
Slash commands system for Drift CLI.

Provides quick, context-aware actions triggered with / prefix.
Examples:
  /git - Suggest git actions based on repo state
  /fix - Suggest fixes for recent errors
  /find - Quick file/content search
  /commit - Smart commit workflow
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import subprocess
from datetime import datetime

from drift_cli.core.memory import MemoryManager


@dataclass
class SlashCommand:
    """Represents a slash command with its metadata."""
    
    name: str
    description: str
    query_template: str  # Template to send to LLM
    category: str  # For grouping: git, files, system, workflow
    requires_git: bool = False
    icon: str = "•"


class SlashCommandRegistry:
    """Registry of available slash commands."""
    
    COMMANDS = {
        # Git commands
        "/git": SlashCommand(
            name="/git",
            description="Suggest next git action based on repo status",
            query_template="Analyze the current git repository status and suggest the next logical action. Check for uncommitted changes, unpushed commits, branches, etc.",
            category="git",
            requires_git=True,
            icon="🔀"
        ),
        "/commit": SlashCommand(
            name="/commit",
            description="Smart commit with generated message",
            query_template="Generate a concise, conventional commit message based on the staged changes. Follow conventional commit format (feat:, fix:, docs:, etc.). Show git add and git commit commands.",
            category="git",
            requires_git=True,
            icon="📝"
        ),
        "/status": SlashCommand(
            name="/status",
            description="Show git status with interpretation",
            query_template="Run git status and explain what each section means. Suggest next actions based on the status.",
            category="git",
            requires_git=True,
            icon="📊"
        ),
        "/push": SlashCommand(
            name="/push",
            description="Safe push workflow",
            query_template="Check if there are commits to push. Verify the remote branch exists. Suggest safe push command with --force-with-lease if needed.",
            category="git",
            requires_git=True,
            icon="⬆️"
        ),
        "/pull": SlashCommand(
            name="/pull",
            description="Safe pull/sync workflow",
            query_template="Pull latest changes safely. Check for local changes first. Suggest stash if needed. Use --rebase if appropriate.",
            category="git",
            requires_git=True,
            icon="⬇️"
        ),
        
        # File operations
        "/find": SlashCommand(
            name="/find",
            description="Smart file and content search",
            query_template="Find files or content in the current directory. Use modern tools like fd, rg, or fallback to find/grep. Safe read-only operations only.",
            category="files",
            icon="🔍"
        ),
        "/recent": SlashCommand(
            name="/recent",
            description="Show recently modified files",
            query_template="List files modified in the last 24 hours, sorted by modification time. Use safe read-only commands.",
            category="files",
            icon="🕐"
        ),
        "/large": SlashCommand(
            name="/large",
            description="Find large files",
            query_template="Find and list large files (>10MB) in current directory and subdirectories. Show sizes in human-readable format.",
            category="files",
            icon="📦"
        ),
        "/tree": SlashCommand(
            name="/tree",
            description="Show directory structure",
            query_template="Display directory tree structure. Use tree command if available, otherwise use find with formatting. Limit depth to 3 levels.",
            category="files",
            icon="🌳"
        ),
        
        # System & diagnosis
        "/fix": SlashCommand(
            name="/fix",
            description="Suggest fixes for recent errors",
            query_template="Analyze recent command errors and environment issues. Suggest specific fixes based on error messages, common patterns, and project context.",
            category="system",
            icon="🔧"
        ),
        "/clean": SlashCommand(
            name="/clean",
            description="Clean project artifacts safely",
            query_template="Identify and safely remove build artifacts, cache files, and temporary files. Suggest commands specific to the project type (node_modules, __pycache__, .next, target, etc.). Ask for confirmation.",
            category="system",
            icon="🧹"
        ),
        "/deps": SlashCommand(
            name="/deps",
            description="Check and update dependencies",
            query_template="Check project dependencies based on project type. For Python: check pip/requirements. For Node: check package.json. Suggest update commands if needed.",
            category="system",
            icon="📚"
        ),
        "/port": SlashCommand(
            name="/port",
            description="Check what's using a port",
            query_template="Find what process is using a specific port. If no port specified, show common development ports (3000, 8080, 5000, etc.) and their status.",
            category="system",
            icon="🔌"
        ),
        
        # Workflow shortcuts
        "/test": SlashCommand(
            name="/test",
            description="Run project tests",
            query_template="Detect project type and run appropriate test command. For Python: pytest. For Node: npm test. For Go: go test. Show verbose output.",
            category="workflow",
            icon="🧪"
        ),
        "/build": SlashCommand(
            name="/build",
            description="Build the project",
            query_template="Detect project type and run appropriate build command. For Python: pip install -e . For Node: npm build. For Go: go build.",
            category="workflow",
            icon="🔨"
        ),
        "/dev": SlashCommand(
            name="/dev",
            description="Start development server",
            query_template="Detect project type and start development server. For Python: uvicorn/flask. For Node: npm run dev. For static: python -m http.server.",
            category="workflow",
            icon="🚀"
        ),
        "/lint": SlashCommand(
            name="/lint",
            description="Run linter/formatter",
            query_template="Detect project type and run appropriate linter. For Python: ruff/black/flake8. For Node: eslint. For Go: gofmt. Show and optionally fix issues.",
            category="workflow",
            icon="✨"
        ),
        
        # Help & learning
        "/help": SlashCommand(
            name="/help",
            description="Show available slash commands",
            query_template="",  # Special case, handled separately
            category="meta",
            icon="❓"
        ),
        "/tips": SlashCommand(
            name="/tips",
            description="Get personalized tips",
            query_template="Based on my command history and patterns, suggest workflow improvements, aliases, or better ways to accomplish common tasks.",
            category="meta",
            icon="💡"
        ),
    }
    
    @classmethod
    def get_command(cls, name: str) -> Optional[SlashCommand]:
        """Get a slash command by name."""
        return cls.COMMANDS.get(name.lower())
    
    @classmethod
    def list_commands(cls, category: Optional[str] = None) -> List[SlashCommand]:
        """List all commands, optionally filtered by category."""
        commands = cls.COMMANDS.values()
        if category:
            commands = [cmd for cmd in commands if cmd.category == category]
        return sorted(commands, key=lambda c: c.name)
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Get list of all categories."""
        return sorted(set(cmd.category for cmd in cls.COMMANDS.values()))
    
    @classmethod
    def search(cls, query: str) -> List[SlashCommand]:
        """Search commands by name or description."""
        query_lower = query.lower()
        return [
            cmd for cmd in cls.COMMANDS.values()
            if query_lower in cmd.name.lower() or query_lower in cmd.description.lower()
        ]


class SlashCommandHandler:
    """Handles execution of slash commands with context awareness."""
    
    def __init__(self, memory: Optional[MemoryManager] = None):
        """Initialize handler with optional memory for personalization."""
        self.memory = memory or MemoryManager()
        self.registry = SlashCommandRegistry()
    
    def is_slash_command(self, query: str) -> bool:
        """Check if query is a slash command."""
        return query.strip().startswith("/")
    
    def parse_slash_command(self, query: str) -> tuple[str, str]:
        """
        Parse slash command into command name and arguments.
        
        Returns:
            (command_name, args)
        
        Examples:
            "/git" -> ("/git", "")
            "/find *.py" -> ("/find", "*.py")
            "/port 3000" -> ("/port", "3000")
        """
        parts = query.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        return command, args
    
    def check_requirements(self, command: SlashCommand) -> tuple[bool, Optional[str]]:
        """
        Check if requirements for command are met.
        
        Returns:
            (ok, error_message)
        """
        if command.requires_git:
            if not self._is_git_repo():
                return False, "Not in a git repository"
        
        return True, None
    
    def _is_git_repo(self) -> bool:
        """Check if current directory is in a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _get_git_context(self) -> Dict[str, Any]:
        """Get current git repository context."""
        context = {}
        
        try:
            # Branch name
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                context["branch"] = result.stdout.strip()
            
            # Uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                changes = result.stdout.strip().split("\n") if result.stdout.strip() else []
                context["uncommitted_files"] = len(changes)
                context["has_changes"] = len(changes) > 0
            
            # Unpushed commits
            result = subprocess.run(
                ["git", "log", "@{u}..", "--oneline"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                commits = result.stdout.strip().split("\n") if result.stdout.strip() else []
                context["unpushed_commits"] = len(commits)
            
            # Staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                staged = result.stdout.strip().split("\n") if result.stdout.strip() else []
                context["staged_files"] = len(staged)
        
        except Exception:
            pass
        
        return context
    
    def enhance_query(self, command: SlashCommand, args: str) -> str:
        """
        Enhance the command query template with context and arguments.
        
        Returns:
            Full query string to send to LLM
        """
        query_parts = [command.query_template]
        
        # Add arguments if provided
        if args:
            query_parts.append(f"\nUser specification: {args}")
        
        # Add git context if git command
        if command.requires_git:
            git_ctx = self._get_git_context()
            if git_ctx:
                query_parts.append("\nCurrent Git Status:")
                if "branch" in git_ctx:
                    query_parts.append(f"- Branch: {git_ctx['branch']}")
                if "uncommitted_files" in git_ctx:
                    query_parts.append(f"- Uncommitted files: {git_ctx['uncommitted_files']}")
                if "staged_files" in git_ctx:
                    query_parts.append(f"- Staged files: {git_ctx['staged_files']}")
                if "unpushed_commits" in git_ctx:
                    query_parts.append(f"- Unpushed commits: {git_ctx['unpushed_commits']}")
        
        # Add project context
        if self.memory.context.detected_project_type:
            query_parts.append(f"\nProject type: {self.memory.context.detected_project_type}")
        
        # Add recent errors if using /fix
        if command.name == "/fix" and self.memory.context.recent_errors:
            query_parts.append("\nRecent errors:")
            for error in self.memory.context.recent_errors[-3:]:
                error_msg = error.get('error', {}).get('message', 'Unknown')
                query_parts.append(f"- {error_msg}")
        
        # Add memory preferences
        if self.memory.preferences.favorite_tools:
            tools = ", ".join(self.memory.preferences.favorite_tools[:5])
            query_parts.append(f"\nPreferred tools: {tools}")
        
        return "\n".join(query_parts)
    
    def process_slash_command(self, query: str) -> tuple[bool, str, Optional[str]]:
        """
        Process a slash command.
        
        Returns:
            (is_slash_command, enhanced_query, error_message)
        
        If is_slash_command is False, return original query.
        If error_message is not None, command failed validation.
        """
        if not self.is_slash_command(query):
            return False, query, None
        
        command_name, args = self.parse_slash_command(query)
        
        # Special case: /help
        if command_name == "/help":
            return True, "", None  # Will be handled specially by CLI
        
        # Get command from registry
        command = self.registry.get_command(command_name)
        if not command:
            # Try to search for similar commands
            similar = self.registry.search(command_name[1:])  # Remove leading /
            if similar:
                suggestions = ", ".join(cmd.name for cmd in similar[:3])
                error = f"Unknown command: {command_name}\nDid you mean: {suggestions}?"
            else:
                error = f"Unknown command: {command_name}\nUse /help to see available commands"
            return True, "", error
        
        # Check requirements
        ok, error = self.check_requirements(command)
        if not ok:
            return True, "", f"Cannot run {command_name}: {error}"
        
        # Enhance query with context
        enhanced_query = self.enhance_query(command, args)
        
        return True, enhanced_query, None
    
    def get_help_text(self) -> str:
        """Generate help text for all slash commands."""
        lines = [
            "🎯 Drift Slash Commands - Quick Context-Aware Actions\n",
            "Type a slash command and press Enter to get smart suggestions.\n"
        ]
        
        categories = self.registry.get_categories()
        for category in categories:
            if category == "meta":
                continue
            
            lines.append(f"\n[bold cyan]{category.upper()}[/bold cyan]")
            commands = self.registry.list_commands(category)
            for cmd in commands:
                lines.append(f"  {cmd.icon} {cmd.name:<12} {cmd.description}")
        
        # Meta commands last
        lines.append(f"\n[bold cyan]HELP[/bold cyan]")
        for cmd in self.registry.list_commands("meta"):
            lines.append(f"  {cmd.icon} {cmd.name:<12} {cmd.description}")
        
        lines.append("\n[dim]Examples:")
        lines.append("  /git               - Suggest next git action")
        lines.append("  /find *.py         - Find all Python files")
        lines.append("  /port 3000         - Check what's using port 3000")
        lines.append("  /commit            - Smart commit with AI message[/dim]")
        
        return "\n".join(lines)
