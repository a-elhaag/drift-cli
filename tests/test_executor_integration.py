"""Integration tests using mock and local executors in sandbox."""

import pytest
from pathlib import Path

from drift_cli.core.executor_base import MockExecutor, LocalExecutor, get_executor


class TestMockExecutor:
    """Test mock executor (safest - no actual execution)."""

    def test_mock_executor_logs_commands(self, mock_executor):
        """Mock executor should log all commands without executing."""
        result = mock_executor.execute("echo 'Hello'")

        assert result.exit_code == 0
        assert result.was_dry_run is True
        assert len(mock_executor.get_log()) == 1
        assert "echo" in mock_executor.get_log()[0]["command"]

    def test_mock_executor_multiple_commands(self, mock_executor):
        """Mock executor can log multiple commands."""
        mock_executor.execute("ls")
        mock_executor.execute("cat file.txt")
        mock_executor.execute("grep pattern file.txt")

        assert len(mock_executor.get_log()) == 3

    def test_mock_executor_safety_preserved(self, mock_executor):
        """Mock executor should log dangerous commands too."""
        result = mock_executor.execute("rm -rf /")

        assert result.exit_code == 0
        assert result.was_dry_run is True
        # Command is logged, not executed
        assert len(mock_executor.get_log()) == 1


class TestLocalExecutor:
    """Test local executor (real execution in sandbox)."""

    def test_local_executor_dry_run(self, local_executor):
        """Local executor in dry-run mode should not execute."""
        local_executor.dry_run = True
        result = local_executor.execute("touch file.txt")

        assert result.exit_code == 0
        assert result.was_dry_run is True
        # No file created
        assert not (local_executor.sandbox_root / "file.txt").exists()

    def test_local_executor_creates_files(self, local_executor):
        """Local executor can create files in sandbox."""
        local_executor.dry_run = False
        result = local_executor.execute("touch test_file.txt")

        assert result.exit_code == 0
        assert (local_executor.sandbox_root / "test_file.txt").exists()

    def test_local_executor_runs_in_sandbox(self, local_executor):
        """Local executor runs commands in sandbox directory."""
        local_executor.dry_run = False
        result = local_executor.execute("pwd")

        assert result.exit_code == 0
        assert str(local_executor.sandbox_root) in result.stdout.strip()

    def test_local_executor_timeout(self, local_executor):
        """Local executor should timeout long-running commands."""
        local_executor.dry_run = False
        result = local_executor.execute("sleep 60")

        assert result.exit_code == -1
        assert "timed out" in result.stderr.lower()


class TestExecutorFactory:
    """Test executor factory."""

    def test_get_mock_executor(self, temp_sandbox):
        """Factory should create mock executor."""
        executor = get_executor("mock", temp_sandbox)
        assert isinstance(executor, MockExecutor)

    def test_get_local_executor(self, temp_sandbox):
        """Factory should create local executor."""
        executor = get_executor("local", temp_sandbox)
        assert isinstance(executor, LocalExecutor)

    def test_invalid_executor_mode(self, temp_sandbox):
        """Factory should reject invalid modes."""
        with pytest.raises(ValueError):
            get_executor("invalid", temp_sandbox)


class TestSandboxIsolation:
    """Test that sandbox isolation works."""

    def test_cannot_escape_sandbox_with_mock(self, mock_executor):
        """Mock executor should safely handle escaping attempts."""
        # This is logged but not executed
        result = mock_executor.execute("cd / && rm -rf *")
        assert result.was_dry_run is True

    def test_local_executor_creates_in_sandbox_only(self, local_executor):
        """Local executor should only create files in sandbox."""
        local_executor.dry_run = False

        # Create a file
        local_executor.execute("echo 'test' > sandbox_file.txt")

        # File should exist in sandbox
        assert (local_executor.sandbox_root / "sandbox_file.txt").exists()

        # Should not exist outside sandbox
        assert not Path("/sandbox_file.txt").exists()


class TestExecutionResult:
    """Test ExecutionResult data structure."""

    def test_result_has_timing_info(self, mock_executor):
        """Result should include timing information."""
        result = mock_executor.execute("test command")

        assert hasattr(result, "duration_ms")
        assert result.duration_ms >= 0

    def test_result_tracks_dry_run_status(self, mock_executor):
        """Result should track if it was a dry run."""
        result = mock_executor.execute("test")
        assert result.was_dry_run is True

    def test_result_contains_output(self, local_executor):
        """Result should contain stdout/stderr."""
        local_executor.dry_run = False
        result = local_executor.execute("echo 'hello'")

        assert result.stdout  # Has output
        assert result.exit_code == 0
