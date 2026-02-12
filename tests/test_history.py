"""Tests for history and snapshot management."""

import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta

from drift_cli.core.history import HistoryManager
from drift_cli.models import Plan, Command, RiskLevel, HistoryEntry


def _make_plan(summary="test plan", risk=RiskLevel.LOW):
    """Helper to create a minimal Plan."""
    return Plan(
        summary=summary,
        risk=risk,
        commands=[Command(command="echo test", description="test cmd")],
        explanation="test explanation",
    )


class TestHistoryAddAndRetrieve:
    """Test adding and retrieving history entries."""

    def test_add_entry(self, tmp_path):
        """Adding an entry should persist it."""
        hm = HistoryManager(drift_dir=tmp_path)
        entry = hm.add_entry(query="list files", plan=_make_plan(), executed=True, exit_code=0)

        assert isinstance(entry, HistoryEntry)
        assert entry.query == "list files"
        assert entry.executed is True

    def test_get_history_returns_entries(self, tmp_path):
        """get_history should return added entries."""
        hm = HistoryManager(drift_dir=tmp_path)
        hm.add_entry(query="first", plan=_make_plan(), executed=True)
        hm.add_entry(query="second", plan=_make_plan(), executed=False)

        history = hm.get_history(limit=10)
        assert len(history) == 2

    def test_get_history_respects_limit(self, tmp_path):
        """get_history should respect the limit parameter."""
        hm = HistoryManager(drift_dir=tmp_path)
        for i in range(20):
            hm.add_entry(query=f"query {i}", plan=_make_plan(), executed=True)

        history = hm.get_history(limit=5)
        assert len(history) == 5

    def test_get_history_empty(self, tmp_path):
        """get_history on empty history should return empty list."""
        hm = HistoryManager(drift_dir=tmp_path)
        assert hm.get_history() == []

    def test_get_last_entry(self, tmp_path):
        """get_last_entry should return most recent entry."""
        hm = HistoryManager(drift_dir=tmp_path)
        hm.add_entry(query="old", plan=_make_plan(), executed=True)
        hm.add_entry(query="new", plan=_make_plan(), executed=True)

        last = hm.get_last_entry()
        assert last is not None
        assert last.query == "new"

    def test_get_last_entry_empty(self, tmp_path):
        """get_last_entry on empty history should return None."""
        hm = HistoryManager(drift_dir=tmp_path)
        assert hm.get_last_entry() is None


class TestSnapshotManagement:
    """Test snapshot creation, restore, and listing."""

    def test_create_snapshot(self, tmp_path):
        """Creating a snapshot should return a valid ID."""
        hm = HistoryManager(drift_dir=tmp_path)

        # Create a file to snapshot
        test_file = tmp_path / "testfile.txt"
        test_file.write_text("original content")

        snapshot_id = hm.create_snapshot([str(test_file)])
        assert snapshot_id
        assert (tmp_path / "snapshots" / snapshot_id / "metadata.json").exists()

    def test_create_snapshot_nonexistent_file(self, tmp_path):
        """Snapshotting nonexistent files should not crash."""
        hm = HistoryManager(drift_dir=tmp_path)
        snapshot_id = hm.create_snapshot(["/this/does/not/exist.txt"])
        assert snapshot_id  # Still returns an ID, just no files snapshotted

    def test_list_snapshots(self, tmp_path):
        """list_snapshots should return all created snapshots."""
        hm = HistoryManager(drift_dir=tmp_path)
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        hm.create_snapshot([str(test_file)])
        hm.create_snapshot([str(test_file)])

        snapshots = hm.list_snapshots()
        assert len(snapshots) == 2

    def test_list_snapshots_empty(self, tmp_path):
        """list_snapshots with no snapshots returns empty list."""
        hm = HistoryManager(drift_dir=tmp_path)
        assert hm.list_snapshots() == []

    def test_restore_snapshot_invalid_id(self, tmp_path):
        """Restoring with invalid ID should return False."""
        hm = HistoryManager(drift_dir=tmp_path)
        assert hm.restore_snapshot("nonexistent-id") is False

    def test_restore_snapshot_path_traversal(self, tmp_path):
        """Snapshot IDs with path traversal should be rejected."""
        hm = HistoryManager(drift_dir=tmp_path)
        assert hm.restore_snapshot("../../etc") is False
        assert hm.restore_snapshot("../passwd") is False
        assert hm.restore_snapshot(".hidden") is False

    def test_cleanup_old_snapshots_keeps_recent(self, tmp_path):
        """Cleanup should keep the most recent snapshots."""
        hm = HistoryManager(drift_dir=tmp_path)
        test_file = tmp_path / "file.txt"
        test_file.write_text("data")

        for _ in range(5):
            hm.create_snapshot([str(test_file)])

        deleted = hm.cleanup_old_snapshots(keep=5, max_age_days=0)
        assert deleted == 0  # All within keep limit


class TestHistoryRotation:
    """Test history file rotation."""

    def test_rotation_not_triggered_for_small_files(self, tmp_path):
        """Rotation should not happen for small history files."""
        hm = HistoryManager(drift_dir=tmp_path)
        for i in range(10):
            hm.add_entry(query=f"q{i}", plan=_make_plan(), executed=True)

        # No archive files should exist
        archives = list(tmp_path.glob("history.*.jsonl"))
        assert len(archives) == 0


class TestPathSafety:
    """Test path validation for safety."""

    def test_valid_path_within_root(self, tmp_path):
        """Paths within allowed roots should be valid."""
        hm = HistoryManager(drift_dir=tmp_path)
        test_path = tmp_path / "subdir" / "file.txt"
        assert hm._validate_path_safety(test_path, [tmp_path]) is True

    def test_invalid_path_outside_root(self, tmp_path):
        """Paths outside allowed roots should be invalid."""
        hm = HistoryManager(drift_dir=tmp_path)
        assert hm._validate_path_safety(Path("/etc/passwd"), [tmp_path]) is False
