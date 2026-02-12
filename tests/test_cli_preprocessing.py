"""Tests for CLI argument preprocessing."""

import sys
import pytest

from drift_cli.cli import _preprocess_argv, _SUBCOMMANDS


class TestPreprocessArgv:
    """Test the _preprocess_argv function that normalizes multi-word queries."""

    def _run(self, args):
        """Helper: set sys.argv, run preprocessing, return result."""
        sys.argv = ["drift"] + args
        _preprocess_argv()
        return sys.argv[1:]  # Return everything after "drift"

    def test_no_args(self):
        """No arguments should not modify argv."""
        result = self._run([])
        assert result == []

    def test_single_subcommand(self):
        """Known subcommand alone should not be modified."""
        result = self._run(["doctor"])
        assert result == ["doctor"]

    def test_subcommand_with_single_arg(self):
        """Subcommand with a single arg should not be modified."""
        result = self._run(["find", "something"])
        assert result == ["find", "something"]

    # --- Case 1: unknown first word → rewrite to suggest ---

    def test_unknown_word_becomes_suggest(self):
        """Single unknown word should become 'suggest <word>'."""
        result = self._run(["hello"])
        assert result == ["suggest", "hello"]

    def test_multi_word_query_becomes_suggest(self):
        """Multiple unknown words should become 'suggest <joined>'."""
        result = self._run(["list", "all", "files"])
        assert result == ["suggest", "list all files"]

    def test_quoted_query_becomes_suggest(self):
        """Quoted query (not a subcommand) should become suggest."""
        result = self._run(["list all files"])
        assert result == ["suggest", "list all files"]

    # --- Case 2/3: subcommand + multi-word query → join positional args ---

    def test_find_multi_word(self):
        """'find' with multiple words should join them."""
        result = self._run(["find", "js", "files"])
        assert result == ["find", "js files"]

    def test_suggest_multi_word(self):
        """'suggest' with multiple words should join them."""
        result = self._run(["suggest", "list", "all", "python", "files"])
        assert result == ["suggest", "list all python files"]

    def test_explain_multi_word(self):
        """'explain' with multiple words should join them."""
        result = self._run(["explain", "ls", "-la"])
        # -la is an option-like arg, only positional gets joined
        # "ls" is the only positional → no change (only 1 positional)
        assert result == ["explain", "ls", "-la"]

    def test_suggest_with_options(self):
        """Options should be preserved, positional args joined."""
        result = self._run(["suggest", "-d", "list", "all", "files"])
        assert result == ["suggest", "-d", "list all files"]

    def test_suggest_with_long_option(self):
        """Long options like --dry-run should be preserved."""
        result = self._run(["suggest", "--dry-run", "show", "disk", "usage"])
        assert result == ["suggest", "--dry-run", "show disk usage"]

    def test_find_with_quoted_arg(self):
        """Already-quoted arg should not be modified."""
        result = self._run(["find", "js files"])
        assert result == ["find", "js files"]

    # --- Edge cases ---

    def test_option_first_no_rewrite(self):
        """Args starting with '-' should not be rewritten."""
        result = self._run(["--help"])
        assert result == ["--help"]

    def test_non_query_subcommand_unmodified(self):
        """Subcommands that don't take queries should not be modified."""
        result = self._run(["history", "--limit", "5"])
        assert result == ["history", "--limit", "5"]

    def test_all_subcommands_recognized(self):
        """Sanity: known subcommands set should include the important ones."""
        for cmd in ["suggest", "find", "explain", "history", "doctor",
                     "config", "undo", "again", "version", "memory"]:
            assert cmd in _SUBCOMMANDS
