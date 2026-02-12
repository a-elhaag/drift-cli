"""
Testing utilities for Drift CLI.

Provides:
- Temporary sandbox setup/cleanup
- Test executor instances
- Test data fixtures
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from drift_cli.core.executor_base import MockExecutor, LocalExecutor, get_executor


@pytest.fixture
def temp_sandbox() -> Generator[Path, None, None]:
    """
    Provide a temporary sandbox directory.
    
    Creates a temp dir, yields it, then cleans up.
    Perfect for safe testing without touching real files.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="drift_sandbox_"))
    try:
        yield temp_dir
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_executor(temp_sandbox) -> MockExecutor:
    """Provide a mock executor for safe testing."""
    return get_executor("mock", temp_sandbox)


@pytest.fixture
def local_executor(temp_sandbox) -> LocalExecutor:
    """Provide a local executor with sandbox isolation."""
    return get_executor("local", temp_sandbox)


@pytest.fixture
def test_files(temp_sandbox) -> dict:
    """Create test files in sandbox."""
    files = {
        "file1.txt": temp_sandbox / "file1.txt",
        "file2.py": temp_sandbox / "file2.py",
        "subdir/file3.txt": temp_sandbox / "subdir" / "file3.txt",
    }

    # Create files
    (temp_sandbox / "subdir").mkdir(exist_ok=True)

    files["file1.txt"].write_text("Hello, World!")
    files["file2.py"].write_text("print('Python')\n")
    files["subdir/file3.txt"].write_text("Nested file")

    return files
