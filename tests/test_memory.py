from drift_cli.core.memory import MemoryManager, UserPreference


def test_merge_preferences_project_overrides_scalars(tmp_path):
    manager = MemoryManager(drift_dir=tmp_path / "drift", use_project_memory=False)

    project = UserPreference(
        comfortable_with_high_risk=False,
        prefers_dry_run=False,
        favorite_tools=["rg", "git"],
        avoided_patterns=["rm -rf"],
        common_sequences=[["git", "status"]],
        frequent_directories=["/project"],
        prefers_verbose_explanations=False,
        likes_alternative_suggestions=False,
    )
    global_prefs = UserPreference(
        comfortable_with_high_risk=True,
        prefers_dry_run=True,
        favorite_tools=["git", "pytest"],
        avoided_patterns=["sudo"],
        common_sequences=[["git", "status"], ["pytest", "-q"]],
        frequent_directories=["/home"],
        prefers_verbose_explanations=True,
        likes_alternative_suggestions=True,
    )

    merged = manager._merge_preferences(
        project_prefs=project,
        global_prefs=global_prefs,
        project_fields={
            "comfortable_with_high_risk",
            "prefers_dry_run",
            "prefers_verbose_explanations",
            "likes_alternative_suggestions",
        },
    )

    assert merged.comfortable_with_high_risk is False
    assert merged.prefers_dry_run is False
    assert merged.prefers_verbose_explanations is False
    assert merged.likes_alternative_suggestions is False
    assert merged.favorite_tools == ["rg", "git", "pytest"]
    assert merged.avoided_patterns == ["rm -rf", "sudo"]
    assert merged.common_sequences == [["git", "status"], ["pytest", "-q"]]
    assert merged.frequent_directories == ["/project", "/home"]


def test_update_context_detects_python_project(fake_home, monkeypatch):
    project_dir = fake_home / "repo"
    project_dir.mkdir(parents=True)
    (project_dir / "pyproject.toml").write_text("[project]\nname='demo'\n")
    monkeypatch.chdir(project_dir)

    memory = MemoryManager(drift_dir=fake_home / ".drift", use_project_memory=False)
    memory.update_context(query="run tests")

    assert memory.context.detected_project_type == "python"
    assert memory.context.recent_queries[-1] == "run tests"
