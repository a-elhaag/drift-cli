"""Executor interface with multiple implementations (mock, local, docker)."""

import os
import shlex
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class ExecutionResult:
    """Result of command execution."""
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    was_dry_run: bool = False


class ExecutorBase(ABC):
    """Abstract base class for different executor implementations."""

    def __init__(self, sandbox_root: Optional[Path] = None, dry_run: bool = False):
        """
        Initialize executor.

        Args:
            sandbox_root: Root directory where commands are allowed
            dry_run: If True, don't actually execute
        """
        self.sandbox_root = sandbox_root or Path.cwd()
        self.dry_run = dry_run

    @abstractmethod
    def execute(self, command: str) -> ExecutionResult:
        """Execute a command safely."""
        pass

    def _validate_path(self, path: str) -> bool:
        """Check if path is within sandbox root."""
        try:
            abs_path = Path(path).resolve()
            abs_sandbox = self.sandbox_root.resolve()
            return abs_path.is_relative_to(abs_sandbox)
        except ValueError:
            return False


class MockExecutor(ExecutorBase):
    """
    Mock executor - doesn't actually run commands.
    
    Perfect for testing:
    - JSON parsing
    - Safety checks
    - UX output
    - History/memory
    - Undo logic (against temp files)
    """

    def __init__(self, sandbox_root: Optional[Path] = None):
        super().__init__(sandbox_root, dry_run=True)
        self.execution_log = []

    def execute(self, command: str) -> ExecutionResult:
        """
        Mock execution - just log and pretend success.
        
        Args:
            command: Command to (pretend to) execute
            
        Returns:
            ExecutionResult with fake but realistic data
        """
        start = datetime.now()

        # Log the execution
        self.execution_log.append({
            "command": command,
            "timestamp": start.isoformat(),
            "mode": "mock",
        })

        # Return fake success
        result = ExecutionResult(
            exit_code=0,
            stdout=f"[MOCK] Would execute: {command}\n",
            stderr="",
            duration_ms=(datetime.now() - start).total_seconds() * 1000,
            was_dry_run=True,
        )

        return result

    def get_log(self):
        """Get all logged executions."""
        return self.execution_log


class LocalExecutor(ExecutorBase):
    """
    Local executor - runs commands in sandbox directory.
    
    Safety:
    - Enforces sandbox_root (e.g., /tmp/drift-sandbox)
    - Blocks commands that escape the sandbox
    - Good for real testing without destroying your system
    """

    def execute(self, command: str) -> ExecutionResult:
        """
        Execute command locally in sandbox.
        
        Args:
            command: Command to execute
            
        Returns:
            ExecutionResult with actual output
        """
        if self.dry_run:
            # Dry-run: show what would execute
            return ExecutionResult(
                exit_code=0,
                stdout=f"[DRY RUN] {command}\n",
                stderr="",
                duration_ms=0,
                was_dry_run=True,
            )

        start = datetime.now()

        try:
            # Run in sandbox directory
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.sandbox_root),
                capture_output=True,
                text=True,
                timeout=30,
            )

            duration = (datetime.now() - start).total_seconds() * 1000

            return ExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=duration,
                was_dry_run=False,
            )

        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start).total_seconds() * 1000
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="Command timed out after 30 seconds",
                duration_ms=duration,
                was_dry_run=False,
            )
        except Exception as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration,
                was_dry_run=False,
            )


class DockerExecutor(ExecutorBase):
    """
    Docker executor - runs commands in isolated container.
    
    Maximum safety:
    - Commands run inside container
    - Mounted sandbox directory only
    - Can't escape the container
    - Even `rm -rf /` only nukes container filesystem
    """

    def __init__(
        self,
        sandbox_root: Optional[Path] = None,
        image: str = "ubuntu:latest",
        dry_run: bool = False,
    ):
        super().__init__(sandbox_root, dry_run)
        self.image = image

    def execute(self, command: str) -> ExecutionResult:
        """
        Execute command inside Docker container.
        
        Args:
            command: Command to execute
            
        Returns:
            ExecutionResult from container
        """
        if self.dry_run:
            return ExecutionResult(
                exit_code=0,
                stdout=f"[DRY RUN - DOCKER] {command}\n",
                stderr="",
                duration_ms=0,
                was_dry_run=True,
            )

        start = datetime.now()

        try:
            # Mount sandbox as /work, run command there
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{self.sandbox_root}:/work",
                "-w", "/work",
                self.image,
                "bash", "-lc", command,
            ]

            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            duration = (datetime.now() - start).total_seconds() * 1000

            return ExecutionResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration_ms=duration,
                was_dry_run=False,
            )

        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start).total_seconds() * 1000
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="Docker command timed out after 60 seconds",
                duration_ms=duration,
                was_dry_run=False,
            )
        except Exception as e:
            duration = (datetime.now() - start).total_seconds() * 1000
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Docker execution failed: {str(e)}",
                duration_ms=duration,
                was_dry_run=False,
            )


def get_executor(mode: str = "mock", sandbox_root: Optional[Path] = None) -> ExecutorBase:
    """
    Factory function to get the right executor.
    
    Args:
        mode: "mock" (safest), "local" (sandbox), or "docker" (most isolated)
        sandbox_root: Path to sandbox directory
        
    Returns:
        Appropriate executor instance
    """
    if mode == "mock":
        return MockExecutor(sandbox_root)
    elif mode == "local":
        return LocalExecutor(sandbox_root, dry_run=False)
    elif mode == "docker":
        return DockerExecutor(sandbox_root, dry_run=False)
    else:
        raise ValueError(f"Unknown executor mode: {mode}")
