"""Tests for memory and context management."""

import json
import pytest
from pathlib import Path
from dataclasses import asdict

from drift_cli.core.memory import (
    MemoryManager,
    UserPreference,
    UserContext,
)
from drift_cli.models import Plan, Command, RiskLevel, HistoryEntry


def _make_plan(risk=RiskLevel.LOW, commands=None):
    """Helper to create a Plan."""
    return Plan(
        summary="test",
        risk=risk,
        commands=commands or [Command(command="echo test", description="test")],
        explanation="test",
    )


def _make_entry(query="test", executed=True, risk=RiskLevel.LOW, commands=None):
    """Helper to create a HistoryEntry."""
    return HistoryEntry(
        timestamp="2026-01-01T00:00:00",
        query=query,
        plan=_make_plan(risk=risk, commands=commands),
        executed=executed,
    )


class TestUserPreference:
    """Test UserPreference defaults."""

    def test_defaults(self):
        """Default preferences should be conservative."""
        prefs = UserPreference()
        assert prefs.comfortable_with_high_risk is False
        assert prefs.prefers_dry_run is True
        assert prefs.favorite_tools == []
        assert prefs.avoided_patterns == []

    def test_mutable_defaults_are_independent(self):
        """Each instance should have independent lists."""
        p1 = UserPreference()
        p2 = UserPreference()
        p1.favorite_tools.append("git")
        assert "git" not in p2.favorite_tools


class TestUserContext:
    """Test UserContext."""

    def test_requires_current_directory(self):
        """UserContext must have a current_directory."""
        ctx = UserContext(current_directory="/tmp")
        assert ctx.current_directory == "/tmp"
        assert ctx.recent_queries == []
        assert ctx.detected_project_type is None


class TestMemoryManager:
    """Test MemoryManager learning and persistence."""

    def test_init_creates_directories(self, tmp_path):
        """MemoryManager should create its directories."""
        drift_dir = tmp_path / "drift"
        mm = MemoryManager(drift_dir=drift_dir, use_project_memory=False)
        assert drift_dir.exists()
        assert (drift_dir / "projects").exists()

    def test_default_preferences_on_fresh_init(self, tmp_path):
        """Fresh MemoryManager should have default preferences."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        assert mm.preferences.comfortable_with_high_risk is False
        assert mm.preferences.favorite_tools == []

    def test_learn_from_history_tool_preferences(self, tmp_path):
        """Learning from history should identify favorite tools."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)

        history = [
            _make_entry(commands=[Command(command="git status", description="check status")]),
            _make_entry(commands=[Command(command="git log", description="view log")]),
            _make_entry(commands=[Command(command="git push", description="push")]),
            _make_entry(commands=[Command(command="ls -la", description="list")]),
        ]

        mm.learn_from_history(history)
        assert "git" in mm.preferences.favorite_tools

    def test_learn_from_history_risk_tolerance(self, tmp_path):
        """Learning should detect high-risk tolerance."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)

        # User executed most high-risk commands
        history = [
            _make_entry(executed=True, risk=RiskLevel.HIGH),
            _make_entry(executed=True, risk=RiskLevel.HIGH),
            _make_entry(executed=True, risk=RiskLevel.HIGH),
            _make_entry(executed=False, risk=RiskLevel.HIGH),
        ]

        mm.learn_from_history(history)
        assert mm.preferences.comfortable_with_high_risk is True  # 75% acceptance

    def test_learn_from_history_low_risk_tolerance(self, tmp_path):
        """Learning should detect conservative users."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)

        # User rejected most high-risk commands
        history = [
            _make_entry(executed=False, risk=RiskLevel.HIGH),
            _make_entry(executed=False, risk=RiskLevel.HIGH),
            _make_entry(executed=True, risk=RiskLevel.HIGH),
        ]

        mm.learn_from_history(history)
        assert mm.preferences.comfortable_with_high_risk is False  # 33% acceptance

    def test_learn_from_history_empty(self, tmp_path):
        """Learning from empty history should not crash."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        mm.learn_from_history([])
        assert mm.preferences.favorite_tools == []

    def test_learn_from_execution_success(self, tmp_path):
        """Successful execution should learn tool preferences."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        plan = _make_plan(commands=[Command(command="docker build .", description="build")])

        mm.learn_from_execution(plan, executed=True, success=True)
        assert "docker" in mm.preferences.favorite_tools

    def test_learn_from_execution_rejected(self, tmp_path):
        """Rejected commands should be tracked as avoided."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        plan = _make_plan(commands=[Command(command="rm -rf build/", description="clean")])

        mm.learn_from_execution(plan, executed=False, success=False)
        assert "rm -rf build/" in mm.preferences.avoided_patterns

    def test_learn_from_execution_high_risk_accepted(self, tmp_path):
        """Accepting high-risk execution should update tolerance."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        plan = _make_plan(risk=RiskLevel.HIGH)

        mm.learn_from_execution(plan, executed=True, success=True)
        assert mm.preferences.comfortable_with_high_risk is True

    def test_preferences_persistence(self, tmp_path):
        """Preferences should survive save/reload cycle."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        mm.preferences.favorite_tools = ["git", "npm"]
        mm.preferences.comfortable_with_high_risk = True
        mm._save_preferences()

        mm2 = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        assert "git" in mm2.preferences.favorite_tools
        assert mm2.preferences.comfortable_with_high_risk is True

    def test_enhance_prompt_with_context(self, tmp_path):
        """Prompt enhancement should include user preferences."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        mm.preferences.favorite_tools = ["git", "docker"]

        enhanced = mm.enhance_prompt_with_context("base context")
        assert "PERSONALIZATION CONTEXT" in enhanced
        assert "git" in enhanced

    def test_enhance_prompt_empty_preferences(self, tmp_path):
        """Empty preferences should still return base context."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        result = mm.enhance_prompt_with_context("base context")
        # Should still include some context (conservative preference)
        assert "base context" in result

    def test_avoided_patterns_limited(self, tmp_path):
        """Avoided patterns list should be capped."""
        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)

        for i in range(15):
            plan = _make_plan(commands=[Command(command=f"cmd_{i}", description="x")])
            mm.learn_from_execution(plan, executed=False, success=False)

        assert len(mm.preferences.avoided_patterns) <= 10

    def test_corrupted_memory_file(self, tmp_path):
        """Corrupted memory file should fall back to defaults."""
        memory_file = tmp_path / "memory.json"
        memory_file.write_text("{{{BAD JSON")

        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        assert mm.preferences.favorite_tools == []

    def test_corrupted_context_file(self, tmp_path):
        """Corrupted context file should fall back to defaults."""
        context_file = tmp_path / "context.json"
        context_file.write_text("NOT JSON")

        mm = MemoryManager(drift_dir=tmp_path, use_project_memory=False)
        assert mm.context.current_directory == str(Path.cwd())
