from drift_cli.core.executor import Executor
from drift_cli.core.history import HistoryManager


def test_execute_plan_dry_run_uses_dry_run_command(tmp_path, make_plan, monkeypatch):
    history = HistoryManager(drift_dir=tmp_path / "drift")
    executor = Executor(history_manager=history)

    plan = make_plan(command="echo real", dry_run="echo preview")
    monkeypatch.setattr(
        executor,
        "_run_command",
        lambda _: (_ for _ in ()).throw(RuntimeError("should not run")),
    )

    exit_code, output, snapshot_id = executor.execute_plan(plan, dry_run=True)

    assert exit_code == 0
    assert "[DRY RUN 1] echo preview" in output
    assert snapshot_id is None


def test_execute_plan_mock_mode(tmp_path, make_plan, monkeypatch):
    history = HistoryManager(drift_dir=tmp_path / "drift")
    monkeypatch.setenv("DRIFT_EXECUTOR", "mock")
    executor = Executor(history_manager=history)

    plan = make_plan(command="echo hi")
    exit_code, output, snapshot_id = executor.execute_plan(plan, dry_run=False)

    assert exit_code == 0
    assert "[MOCK 1] Would execute: echo hi" in output
    assert snapshot_id is None


def test_snapshot_respects_auto_snapshot_setting(tmp_path, make_plan, monkeypatch):
    history = HistoryManager(drift_dir=tmp_path / "drift")
    target_file = tmp_path / "target.txt"
    target_file.write_text("content")

    plan = make_plan(command="echo done", affected_files=[str(target_file)])

    executor = Executor(history_manager=history)
    monkeypatch.setattr(executor, "_run_command", lambda _: (0, "ok"))

    monkeypatch.setattr(Executor, "_auto_snapshot_enabled", staticmethod(lambda: False))
    _, _, disabled_snapshot = executor.execute_plan(plan, dry_run=False)
    assert disabled_snapshot is None

    monkeypatch.setattr(Executor, "_auto_snapshot_enabled", staticmethod(lambda: True))
    _, _, enabled_snapshot = executor.execute_plan(plan, dry_run=False)
    assert enabled_snapshot is not None
