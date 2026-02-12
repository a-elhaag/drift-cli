"""Command execution utilities with improved safety and performance."""

import os
import shlex
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

from drift_cli.core.history import HistoryManager
from drift_cli.core.safety import SafetyChecker
from drift_cli.models import Command, Plan


class Executor:
    """Executes commands safely with snapshots and rollback support."""

    def __init__(self, history_manager: Optional[HistoryManager] = None):
        self.history = history_manager or HistoryManager()
        self.executor_mode = os.getenv("DRIFT_EXECUTOR", "local")  # mock, local, docker
        self.sandbox_root = os.getenv("DRIFT_SANDBOX_ROOT")  # Optional sandbox directory
        self._context_cache = None
        self._context_cache_time = 0

    def execute_plan(
        self, plan: Plan, dry_run: bool = False
    ) -> Tuple[int, str, Optional[str]]:
        """
        Execute a plan's commands.

        Args:
            plan: The plan to execute
            dry_run: If True, only show what would be executed

        Returns:
            Tuple of (exit_code, output, snapshot_id)
        """
        # Check for forced dry-run from environment
        if os.getenv("DRIFT_DRY_RUN", "").lower() in ("1", "true", "yes"):
            dry_run = True
        
        # Validate safety
        commands_list = [cmd.command for cmd in plan.commands]
        all_safe, warnings = SafetyChecker.validate_commands(commands_list)

        if not all_safe:
            return 1, "\n".join(warnings), None
        
        # Validate sandbox if enabled
        if self.sandbox_root:
            violation = self._check_sandbox_violation()
            if violation:
                return 1, violation, None

        # Create snapshot if files will be affected
        snapshot_id = None
        if plan.affected_files and not dry_run:
            snapshot_id = self.history.create_snapshot(plan.affected_files)

        # Execute commands
        output_lines = []
        exit_code = 0

        for idx, cmd in enumerate(plan.commands, 1):
            if dry_run:
                # Use dry-run version if available
                command = cmd.dry_run or cmd.command
                output_lines.append(f"[DRY RUN {idx}] {command}")
            else:
                if self.executor_mode == "mock":
                    output_lines.append(f"[MOCK {idx}] Would execute: {cmd.command}")
                else:
                    output_lines.append(f"[{idx}] Executing: {cmd.command}")
                    code, out = self._run_command(cmd.command)
                    exit_code = code
                    if out:
                        output_lines.append(out)

                    # Stop on first failure
                    if code != 0:
                        output_lines.append(f"Command failed with exit code {code}")
                        break

        return exit_code, "\n".join(output_lines), snapshot_id
    
    def _check_sandbox_violation(self) -> Optional[str]:
        """Check if current directory violates sandbox constraints."""
        if not self.sandbox_root:
            return None
        
        cwd = os.getcwd()
        sandbox_path = Path(self.sandbox_root).resolve()
        current_path = Path(cwd).resolve()
        
        try:
            current_path.relative_to(sandbox_path)
            return None
        except ValueError:
            return (
                f"⚠️  SANDBOX VIOLATION: Current directory '{cwd}' is outside "
                f"sandbox root '{self.sandbox_root}'\n"
                f"Set DRIFT_SANDBOX_ROOT to a parent directory or unset it."
            )

    def _run_command(self, command: str) -> Tuple[int, str]:
        """
        Run a single shell command with improved safety.
        
        Uses shell=False when possible to prevent injection.

        Returns:
            Tuple of (exit_code, output)
        """
        try:
            # For complex commands with pipes, redirects, etc., we still need shell=True
            # but we've already validated the command through SafetyChecker
            needs_shell = any(char in command for char in ['|', '>', '<', '&&', '||', ';'])
            
            if needs_shell:
                # Use shell=True for complex commands (already safety-checked)
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    cwd=os.getcwd(),
                    executable='/bin/bash',  # Explicit shell for consistency
                )
            else:
                # Use shell=False for simple commands (safer)
                try:
                    args = shlex.split(command)
                    result = subprocess.run(
                        args,
                        shell=False,
                        capture_output=True,
                        text=True,
                        timeout=300,
                        cwd=os.getcwd(),
                    )
                except ValueError:
                    # shlex.split failed, fall back to shell=True
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=300,
                        cwd=os.getcwd(),
                        executable='/bin/bash',
                    )
            
            output = result.stdout + result.stderr
            return result.returncode, output.strip()
        except subprocess.TimeoutExpired:
            return 1, "Command timed out after 5 minutes"
        except Exception as e:
            return 1, f"Failed to execute: {str(e)}"

    def get_context(self) -> str:
        """
        Get current execution context for the LLM with caching.

        Returns:
            Context string with cwd, user, etc.
        """
        import time
        
        # Cache context for 5 seconds to avoid repeated git calls
        current_time = time.time()
        if self._context_cache and (current_time - self._context_cache_time) < 5:
            return self._context_cache
        
        context_parts = [
            f"Current directory: {os.getcwd()}",
            f"User: {os.getenv('USER', 'unknown')}",
            f"Shell: {os.getenv('SHELL', 'unknown')}",
        ]

        # Add git info if in a git repo
        git_root = self._get_git_root()
        if git_root:
            context_parts.append(f"Git repository: {git_root}")
        
        self._context_cache = "\n".join(context_parts)
        self._context_cache_time = current_time
        
        return self._context_cache
    
    @lru_cache(maxsize=1)
    def _get_git_root(self) -> Optional[str]:
        """Get git root with caching (cached until process restart)."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
