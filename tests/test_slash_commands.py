"""Tests for slash commands system."""

import pytest

from drift_cli.core.slash_commands import (
    SlashCommand,
    SlashCommandRegistry,
    SlashCommandHandler,
)


class TestSlashCommand:
    """Test SlashCommand dataclass."""

    def test_basic_creation(self):
        cmd = SlashCommand(
            name="/test",
            description="Run tests",
            query_template="run tests",
            category="workflow",
        )
        assert cmd.name == "/test"
        assert cmd.requires_git is False
        assert cmd.icon == "•"

    def test_git_command(self):
        cmd = SlashCommand(
            name="/commit",
            description="Commit",
            query_template="commit",
            category="git",
            requires_git=True,
            icon="📝",
        )
        assert cmd.requires_git is True
        assert cmd.icon == "📝"


class TestSlashCommandRegistry:
    """Test SlashCommandRegistry lookups."""

    def test_get_known_command(self):
        """Should find registered commands."""
        cmd = SlashCommandRegistry.get_command("/git")
        assert cmd is not None
        assert cmd.name == "/git"
        assert cmd.requires_git is True

    def test_get_unknown_command(self):
        """Should return None for unknown commands."""
        assert SlashCommandRegistry.get_command("/nonexistent") is None

    def test_case_insensitive_lookup(self):
        """Lookup should be case insensitive."""
        assert SlashCommandRegistry.get_command("/GIT") is not None
        assert SlashCommandRegistry.get_command("/Git") is not None

    def test_list_all_commands(self):
        """Should return all registered commands."""
        cmds = SlashCommandRegistry.list_commands()
        assert len(cmds) > 10  # We have many commands defined
        assert all(isinstance(c, SlashCommand) for c in cmds)

    def test_list_by_category(self):
        """Should filter commands by category."""
        git_cmds = SlashCommandRegistry.list_commands(category="git")
        assert all(c.category == "git" for c in git_cmds)
        assert len(git_cmds) >= 4  # /git, /commit, /status, /push, /pull

    def test_list_nonexistent_category(self):
        """Empty category filter should return empty list."""
        cmds = SlashCommandRegistry.list_commands(category="nonexistent_category")
        assert cmds == []

    def test_get_categories(self):
        """Should return all unique categories."""
        cats = SlashCommandRegistry.get_categories()
        assert "git" in cats
        assert "files" in cats
        assert "system" in cats
        assert "workflow" in cats
        assert "meta" in cats

    def test_search_by_name(self):
        """Search should find commands by name."""
        results = SlashCommandRegistry.search("git")
        names = [c.name for c in results]
        assert "/git" in names

    def test_search_by_description(self):
        """Search should find commands by description."""
        results = SlashCommandRegistry.search("test")
        assert len(results) >= 1
        assert any("test" in c.description.lower() for c in results)

    def test_search_no_results(self):
        """Search with no matches returns empty list."""
        results = SlashCommandRegistry.search("xyznonexistent")
        assert results == []

    def test_all_commands_have_required_fields(self):
        """Every registered command should have name, description, category."""
        for name, cmd in SlashCommandRegistry.COMMANDS.items():
            assert cmd.name, f"{name} missing name"
            assert cmd.description, f"{name} missing description"
            assert cmd.category, f"{name} missing category"
            assert name == cmd.name, f"Key {name} doesn't match cmd.name {cmd.name}"


class TestSlashCommandHandler:
    """Test SlashCommandHandler parsing and detection."""

    def setup_method(self):
        self.handler = SlashCommandHandler.__new__(SlashCommandHandler)
        self.handler.registry = SlashCommandRegistry()

    def test_is_slash_command(self):
        """Should detect slash commands."""
        assert SlashCommandHandler.is_slash_command(self.handler, "/git")
        assert SlashCommandHandler.is_slash_command(self.handler, "/find *.py")
        assert SlashCommandHandler.is_slash_command(self.handler, "  /test  ")

    def test_is_not_slash_command(self):
        """Should not detect regular queries as slash commands."""
        assert not SlashCommandHandler.is_slash_command(self.handler, "list files")
        assert not SlashCommandHandler.is_slash_command(self.handler, "what is /etc")
        assert not SlashCommandHandler.is_slash_command(self.handler, "")

    def test_parse_command_no_args(self):
        """Parse command with no arguments."""
        name, args = self.handler.parse_slash_command("/git")
        assert name == "/git"
        assert args == ""

    def test_parse_command_with_args(self):
        """Parse command with arguments."""
        name, args = self.handler.parse_slash_command("/find *.py")
        assert name == "/find"
        assert args == "*.py"

    def test_parse_command_with_complex_args(self):
        """Parse command with multi-word arguments."""
        name, args = self.handler.parse_slash_command("/port 3000 8080")
        assert name == "/port"
        assert args == "3000 8080"

    def test_parse_command_case_normalized(self):
        """Parsed command name should be lowercase."""
        name, _ = self.handler.parse_slash_command("/GIT")
        assert name == "/git"

    def test_parse_command_strips_whitespace(self):
        """Parse should handle extra whitespace."""
        name, args = self.handler.parse_slash_command("  /test  arg  ")
        assert name == "/test"
        assert "arg" in args
