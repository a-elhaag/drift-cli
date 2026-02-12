from drift_cli.core.memory import MemoryManager
from drift_cli.core.slash_commands import SlashCommandHandler, SlashCommandRegistry


def _build_handler(tmp_path):
    memory = MemoryManager(drift_dir=tmp_path / "drift", use_project_memory=False)
    return SlashCommandHandler(memory=memory)


def test_parse_slash_command(tmp_path):
    handler = _build_handler(tmp_path)
    name, args = handler.parse_slash_command("/find *.py")
    assert name == "/find"
    assert args == "*.py"


def test_unknown_command_suggests_similar(tmp_path):
    handler = _build_handler(tmp_path)
    is_slash, _, error = handler.process_slash_command("/sta")
    assert is_slash is True
    assert error is not None
    assert "Did you mean" in error


def test_git_requirement_is_enforced(tmp_path, monkeypatch):
    handler = _build_handler(tmp_path)
    monkeypatch.setattr(handler, "_is_git_repo", lambda: False)

    is_slash, _, error = handler.process_slash_command("/git")
    assert is_slash is True
    assert error == "Cannot run /git: Not in a git repository"


def test_enhance_query_includes_context(tmp_path, monkeypatch):
    handler = _build_handler(tmp_path)
    handler.memory.context.detected_project_type = "python"
    monkeypatch.setattr(
        handler,
        "_get_git_context",
        lambda: {"branch": "main", "staged_files": 2, "unpushed_commits": 1},
    )

    command = SlashCommandRegistry.get_command("/git")
    assert command is not None

    enhanced = handler.enhance_query(command, "status")
    assert "User specification: status" in enhanced
    assert "Current Git Status" in enhanced
    assert "- Branch: main" in enhanced
    assert "Project type: python" in enhanced
