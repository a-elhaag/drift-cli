"""
Memory and context management for personalized AI experience.

This module learns from user interactions to provide:
- Personalized command suggestions
- Context-aware responses
- Pattern recognition
- Preference learning
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

from drift_cli.models import RiskLevel, Plan, HistoryEntry


@dataclass
class UserPreference:
    """User's learned preferences."""
    
    # Risk tolerance
    comfortable_with_high_risk: bool = False
    prefers_dry_run: bool = True
    
    # Command preferences
    favorite_tools: List[str] = None  # e.g., ["git", "docker", "npm"]
    avoided_patterns: List[str] = None  # Commands user often cancels
    
    # Workflow patterns
    common_sequences: List[List[str]] = None  # Common command chains
    frequent_directories: List[str] = None
    
    # Style preferences
    prefers_verbose_explanations: bool = True
    likes_alternative_suggestions: bool = True
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.favorite_tools is None:
            self.favorite_tools = []
        if self.avoided_patterns is None:
            self.avoided_patterns = []
        if self.common_sequences is None:
            self.common_sequences = []
        if self.frequent_directories is None:
            self.frequent_directories = []


@dataclass
class UserContext:
    """Current user context and session information."""
    
    # Current session
    current_directory: str
    current_git_repo: Optional[str] = None
    current_git_branch: Optional[str] = None
    
    # Recent activity
    recent_queries: List[str] = None
    recent_commands: List[str] = None
    recent_errors: List[Dict] = None  # Failed commands
    
    # Environment context
    detected_project_type: Optional[str] = None  # python, node, go, etc.
    detected_tools: List[str] = None  # Installed tools
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.recent_queries is None:
            self.recent_queries = []
        if self.recent_commands is None:
            self.recent_commands = []
        if self.recent_errors is None:
            self.recent_errors = []
        if self.detected_tools is None:
            self.detected_tools = []


class MemoryManager:
    """
    Manages user memory and context for personalized experience.
    
    Learns from:
    - Command execution patterns
    - Accepted vs rejected suggestions
    - Frequently used tools
    - Common workflows
    - Error patterns
    
    Provides:
    - Personalized suggestions
    - Context-aware prompts
    - Smart defaults
    - Pattern-based recommendations
    
    Supports:
    - Global preferences (across all projects)
    - Project-specific preferences (per git repo)
    """
    
    def __init__(self, drift_dir: Optional[Path] = None, use_project_memory: bool = True):
        """Initialize memory manager.
        
        Args:
            drift_dir: Directory to store memory files
            use_project_memory: Enable project-specific memory (uses git repo as key)
        """
        self.drift_dir = drift_dir or Path.home() / ".drift"
        self.use_project_memory = use_project_memory
        
        # Global memory files
        self.memory_file = self.drift_dir / "memory.json"
        self.context_file = self.drift_dir / "context.json"
        
        # Project-specific memory directory
        self.projects_dir = self.drift_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        self.drift_dir.mkdir(exist_ok=True)
        
        # Detect current project
        self.current_project = self._detect_project() if use_project_memory else None
        
        # Load existing memory (project-specific if available)
        self.preferences = self._load_preferences()
        self.context = self._load_context()
    
    def _detect_project(self) -> Optional[str]:
        """Detect current git project and return a unique identifier."""
        import subprocess
        
        try:
            # Get git repo root
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                repo_root = result.stdout.strip()
                # Use repo directory name as project ID
                # You could also use git remote URL hash for uniqueness
                project_id = Path(repo_root).name
                return project_id
        except Exception:
            pass
        
        return None
    
    def _get_project_memory_file(self) -> Optional[Path]:
        """Get the memory file for current project."""
        if not self.current_project:
            return None
        
        # Create project-specific memory file
        project_file = self.projects_dir / f"{self.current_project}.json"
        return project_file
    
    def _load_preferences(self) -> UserPreference:
        """Load user preferences from disk (project-specific or global)."""
        # Try project-specific first
        if self.use_project_memory and self.current_project:
            project_file = self._get_project_memory_file()
            if project_file and project_file.exists():
                try:
                    with open(project_file, 'r') as f:
                        data = json.load(f)
                        prefs = UserPreference(**data.get("preferences", {}))
                        # Merge with global preferences
                        return self._merge_preferences(prefs, self._load_global_preferences())
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Fall back to global preferences
        return self._load_global_preferences()
    
    def _load_global_preferences(self) -> UserPreference:
        """Load global preferences."""
        if not self.memory_file.exists():
            return UserPreference()
        
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                return UserPreference(**data)
        except (json.JSONDecodeError, TypeError):
            return UserPreference()
    
    def _merge_preferences(self, project_prefs: UserPreference, global_prefs: UserPreference) -> UserPreference:
        """Merge project-specific preferences with global ones.
        
        Project-specific preferences take priority.
        """
        merged = UserPreference()
        
        # Use project preference if it differs from default, else use global
        merged.comfortable_with_high_risk = project_prefs.comfortable_with_high_risk or global_prefs.comfortable_with_high_risk
        merged.prefers_dry_run = project_prefs.prefers_dry_run if project_prefs.favorite_tools else global_prefs.prefers_dry_run
        merged.prefers_verbose_explanations = project_prefs.prefers_verbose_explanations or global_prefs.prefers_verbose_explanations
        
        # Combine tool lists (project tools + global tools)
        merged.favorite_tools = list(set(project_prefs.favorite_tools + global_prefs.favorite_tools))
        merged.avoided_patterns = list(set(project_prefs.avoided_patterns + global_prefs.avoided_patterns))
        merged.common_sequences = project_prefs.common_sequences + global_prefs.common_sequences
        
        return merged
    
    def _load_context(self) -> UserContext:
        """Load current context from disk."""
        if not self.context_file.exists():
            return UserContext(current_directory=str(Path.cwd()))
        
        try:
            with open(self.context_file, 'r') as f:
                data = json.load(f)
                return UserContext(**data)
        except (json.JSONDecodeError, TypeError):
            return UserContext(current_directory=str(Path.cwd()))
    
    def _save_preferences(self):
        """Save preferences to disk (both global and project-specific)."""
        # Always save to global
        with open(self.memory_file, 'w') as f:
            json.dump(asdict(self.preferences), f, indent=2)
        
        # Also save to project-specific if in a project
        if self.use_project_memory and self.current_project:
            project_file = self._get_project_memory_file()
            if project_file:
                project_data = {
                    "project": self.current_project,
                    "last_updated": datetime.now().isoformat(),
                    "preferences": asdict(self.preferences)
                }
                with open(project_file, 'w') as f:
                    json.dump(project_data, f, indent=2)
    
    def _save_context(self):
        """Save context to disk."""
        with open(self.context_file, 'w') as f:
            json.dump(asdict(self.context), f, indent=2)
    
    def learn_from_history(self, history: List[HistoryEntry]):
        """
        Learn user preferences from command history.
        
        Analyzes:
        - Accepted vs rejected commands
        - Risk tolerance
        - Tool preferences
        - Command patterns
        """
        if not history:
            return
        
        # Analyze risk tolerance
        executed_high_risk = sum(
            1 for entry in history 
            if entry.executed and entry.plan.risk == RiskLevel.HIGH
        )
        total_high_risk = sum(
            1 for entry in history 
            if entry.plan.risk == RiskLevel.HIGH
        )
        
        if total_high_risk > 0:
            risk_acceptance_rate = executed_high_risk / total_high_risk
            self.preferences.comfortable_with_high_risk = risk_acceptance_rate > 0.6
        
        # Analyze tool usage
        tool_counter = Counter()
        for entry in history:
            if entry.executed:
                for cmd in entry.plan.commands:
                    # Extract tool name (first word of command)
                    tool = cmd.command.split()[0] if cmd.command else None
                    if tool:
                        tool_counter[tool] += 1
        
        # Update favorite tools (top 10)
        self.preferences.favorite_tools = [
            tool for tool, _ in tool_counter.most_common(10)
        ]
        
        # Find avoided patterns (suggested but not executed)
        avoided = []
        for entry in history:
            if not entry.executed:
                for cmd in entry.plan.commands:
                    avoided.append(cmd.command)
        
        # Keep most common avoided patterns
        if avoided:
            avoided_counter = Counter(avoided)
            self.preferences.avoided_patterns = [
                pattern for pattern, count in avoided_counter.most_common(5)
                if count > 1  # Only if rejected multiple times
            ]
        
        # Detect command sequences
        sequences = []
        for i in range(len(history) - 1):
            if history[i].executed and history[i + 1].executed:
                seq = [
                    cmd.command.split()[0] 
                    for cmd in history[i].plan.commands
                ]
                sequences.append(seq)
        
        if sequences:
            # Keep most common sequences
            seq_counter = Counter(tuple(seq) for seq in sequences)
            self.preferences.common_sequences = [
                list(seq) for seq, _ in seq_counter.most_common(5)
            ]
        
        self._save_preferences()
    
    def learn_from_execution(self, plan, executed: bool, success: bool):
        """
        Learn from command execution in real-time.
        
        Args:
            plan: The Plan object that was executed/rejected
            executed: Whether user chose to execute
            success: Whether execution succeeded (only relevant if executed=True)
        """
        if executed:
            # Learn about successful tools
            if success:
                for cmd in plan.commands:
                    tool = cmd.command.split()[0] if cmd.command else None
                    if tool:
                        # Increment usage count
                        if tool not in self.preferences.favorite_tools:
                            self.preferences.favorite_tools.append(tool)
            
            # Learn about risk tolerance
            if plan.risk == RiskLevel.HIGH:
                self.preferences.comfortable_with_high_risk = True
        else:
            # User rejected the suggestion - learn what to avoid
            for cmd in plan.commands:
                pattern = cmd.command
                if pattern and pattern not in self.preferences.avoided_patterns:
                    # Track patterns that are consistently rejected
                    self.preferences.avoided_patterns.append(pattern)
                    # Keep only most recent 10 avoided patterns
                    self.preferences.avoided_patterns = self.preferences.avoided_patterns[-10:]
        
        self._save_preferences()
    
    def update_context(
        self,
        query: Optional[str] = None,
        executed_commands: Optional[List[str]] = None,
        error: Optional[Dict] = None,
    ):
        """Update current session context."""
        # Update directory
        self.context.current_directory = str(Path.cwd())
        
        # Detect git repo and branch
        import subprocess
        git_dir = Path.cwd()
        while git_dir != git_dir.parent:
            if (git_dir / ".git").exists():
                self.context.current_git_repo = str(git_dir)
                # Get current branch
                try:
                    result = subprocess.run(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True,
                        text=True,
                        check=False,
                        cwd=git_dir
                    )
                    if result.returncode == 0:
                        self.context.current_git_branch = result.stdout.strip()
                except Exception:
                    pass
                break
            git_dir = git_dir.parent
        
        # Update recent queries
        if query:
            self.context.recent_queries.append(query)
            self.context.recent_queries = self.context.recent_queries[-10:]
        
        # Update recent commands
        if executed_commands:
            self.context.recent_commands.extend(executed_commands)
            self.context.recent_commands = self.context.recent_commands[-20:]
        
        # Track errors
        if error:
            self.context.recent_errors.append({
                'timestamp': datetime.now().isoformat(),
                'error': error
            })
            self.context.recent_errors = self.context.recent_errors[-10:]
        
        # Detect project type
        cwd = Path.cwd()
        if (cwd / "package.json").exists():
            self.context.detected_project_type = "node"
        elif (cwd / "pyproject.toml").exists() or (cwd / "setup.py").exists():
            self.context.detected_project_type = "python"
        elif (cwd / "go.mod").exists():
            self.context.detected_project_type = "go"
        elif (cwd / "Cargo.toml").exists():
            self.context.detected_project_type = "rust"
        elif (cwd / "Makefile").exists():
            self.context.detected_project_type = "make"
        
        self._save_context()
    
    def enhance_prompt_with_context(self, base_context: str) -> str:
        """
        Enhance base context with memory insights.
        
        This is called before sending query to LLM to make it aware
        of user preferences and patterns.
        """
        enhancements = []
        
        # Add user preferences
        if self.preferences.favorite_tools:
            tools = ", ".join(self.preferences.favorite_tools[:5])
            enhancements.append(f"User's preferred tools: {tools}")
        
        if self.preferences.comfortable_with_high_risk:
            enhancements.append("User is comfortable with higher-risk operations")
        else:
            enhancements.append("User prefers conservative, safer approaches")
        
        # Add current project context
        if self.context.detected_project_type:
            enhancements.append(f"Detected project: {self.context.detected_project_type}")
        
        if self.context.current_git_branch:
            enhancements.append(f"Git branch: {self.context.current_git_branch}")
        
        # Add recent patterns
        if self.context.recent_queries:
            recent = self.context.recent_queries[-2:]
            enhancements.append(f"Recent queries: {', '.join(recent)}")
        
        if enhancements:
            return f"{base_context}\n\nPERSONALIZATION CONTEXT:\n" + "\n".join(f"- {e}" for e in enhancements)
        
        return base_context
    
    def get_personalized_prompt_context(self) -> str:
        """
        Generate context string to append to LLM prompts.
        
        This makes the AI aware of user preferences and context.
        """
        context_parts = []
        
        # Add user preferences
        context_parts.append("USER PREFERENCES:")
        
        if self.preferences.favorite_tools:
            tools = ", ".join(self.preferences.favorite_tools[:5])
            context_parts.append(f"- Familiar tools: {tools}")
        
        if self.preferences.comfortable_with_high_risk:
            context_parts.append("- User is comfortable with higher-risk operations")
        else:
            context_parts.append("- User prefers safer, conservative approaches")
        
        if self.preferences.avoided_patterns:
            context_parts.append("- User tends to avoid:")
            for pattern in self.preferences.avoided_patterns[:3]:
                context_parts.append(f"  • {pattern}")
        
        # Add current context
        context_parts.append("\nCURRENT CONTEXT:")
        context_parts.append(f"- Directory: {self.context.current_directory}")
        
        if self.context.current_git_repo:
            context_parts.append(f"- Git repo: {self.context.current_git_repo}")
        
        if self.context.detected_project_type:
            context_parts.append(f"- Project type: {self.context.detected_project_type}")
        
        # Add recent activity
        if self.context.recent_queries:
            recent = self.context.recent_queries[-3:]
            context_parts.append("\nRECENT QUERIES:")
            for q in recent:
                context_parts.append(f"- {q}")
        
        if self.context.recent_errors:
            context_parts.append("\nRECENT ERRORS:")
            for err in self.context.recent_errors[-2:]:
                context_parts.append(f"- {err.get('error', {}).get('message', 'Unknown error')}")
        
        return "\n".join(context_parts)
    
    def suggest_based_on_patterns(self, query: str) -> List[str]:
        """
        Suggest commands based on learned patterns.
        
        Returns additional context-aware suggestions.
        """
        suggestions = []
        
        # Check if query matches common workflows
        query_lower = query.lower()
        
        # Git workflow suggestions
        if "commit" in query_lower and self.context.current_git_repo:
            if "git add" in self.preferences.favorite_tools:
                suggestions.append("Consider: git add -p (interactive staging)")
        
        # Project-specific suggestions
        if self.context.detected_project_type == "python":
            if "test" in query_lower:
                suggestions.append("Python project detected. Consider: pytest -v")
            elif "install" in query_lower:
                suggestions.append("Consider: pip install -e . (editable install)")
        
        elif self.context.detected_project_type == "node":
            if "test" in query_lower:
                suggestions.append("Node project detected. Consider: npm test")
            elif "install" in query_lower:
                suggestions.append("Consider: npm ci (clean install)")
        
        # Sequence-based suggestions
        if self.context.recent_commands:
            last_cmd = self.context.recent_commands[-1] if self.context.recent_commands else ""
            last_tool = last_cmd.split()[0] if last_cmd else ""
            
            # Find common next steps
            for sequence in self.preferences.common_sequences:
                if sequence and last_tool == sequence[0] and len(sequence) > 1:
                    next_tool = sequence[1]
                    suggestions.append(f"You often run '{next_tool}' after '{last_tool}'")
        
        return suggestions
    
    def get_smart_defaults(self) -> Dict:
        """
        Return smart defaults based on user preferences.
        
        Used by CLI to adjust behavior.
        """
        return {
            'auto_dry_run': self.preferences.prefers_dry_run,
            'show_alternatives': self.preferences.likes_alternative_suggestions,
            'verbose': self.preferences.prefers_verbose_explanations,
            'risk_threshold': RiskLevel.HIGH if self.preferences.comfortable_with_high_risk else RiskLevel.MEDIUM,
        }
    
    def analyze_command_success_rate(self, history: List[HistoryEntry]) -> Dict[str, float]:
        """
        Analyze success rates of different command types.
        
        Returns dict of tool -> success_rate
        """
        tool_stats = defaultdict(lambda: {'total': 0, 'success': 0})
        
        for entry in history:
            if entry.executed:
                for cmd in entry.plan.commands:
                    tool = cmd.command.split()[0] if cmd.command else "unknown"
                    tool_stats[tool]['total'] += 1
                    if entry.exit_code == 0:
                        tool_stats[tool]['success'] += 1
        
        success_rates = {}
        for tool, stats in tool_stats.items():
            if stats['total'] > 0:
                success_rates[tool] = stats['success'] / stats['total']
        
        return success_rates
    
    def detect_learning_opportunities(self, history: List[HistoryEntry]) -> List[str]:
        """
        Detect patterns where user could benefit from tips.
        
        Returns list of helpful tips based on behavior.
        """
        tips = []
        
        # Detect if user frequently runs same command manually
        if self.context.recent_commands:
            cmd_counter = Counter(self.context.recent_commands)
            for cmd, count in cmd_counter.most_common(3):
                if count > 3:
                    tips.append(
                        f"💡 Tip: You run '{cmd}' often. "
                        f"Consider creating an alias or using 'drift again'"
                    )
        
        # Detect if user avoids certain risk levels
        rejected_high_risk = sum(
            1 for entry in history 
            if not entry.executed and entry.plan.risk == RiskLevel.HIGH
        )
        if rejected_high_risk > 5:
            tips.append(
                "💡 Tip: You often skip high-risk commands. "
                "Drift can suggest safer alternatives with --safe flag"
            )
        
        # Detect if user is in a git repo but rarely uses git
        if self.context.current_git_repo:
            git_usage = sum(
                1 for entry in history[-20:] 
                if entry.executed and any('git' in cmd.command for cmd in entry.plan.commands)
            )
            if git_usage == 0:
                tips.append(
                    "💡 Tip: You're in a git repo. "
                    "Try 'drift suggest check git status' for version control help"
                )
        
        return tips[:3]  # Return top 3 tips
    
    def reset(self):
        """Reset all learned preferences (but keep context)."""
        self.preferences = UserPreference()
        self._save_preferences()


def enhance_prompt_with_memory(base_prompt: str, memory: MemoryManager) -> str:
    """
    Enhance a base prompt with memory/context.
    
    Args:
        base_prompt: The original prompt to send to LLM
        memory: MemoryManager instance
    
    Returns:
        Enhanced prompt with user context
    """
    context = memory.get_personalized_prompt_context()
    
    enhanced = f"""{base_prompt}

{context}

INSTRUCTIONS:
- Use the user's familiar tools when possible
- Respect their risk tolerance preferences
- Consider their recent activity for context
- Suggest alternatives if appropriate
- Be aware of the current project type
"""
    
    return enhanced
