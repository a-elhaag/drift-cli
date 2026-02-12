from types import SimpleNamespace

import pytest
import typer

from drift_cli.commands import system_cmd


def _result(code=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=code, stdout=stdout, stderr=stderr)


def test_update_handles_missing_upstream(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[:2] == ["git", "fetch"]:
            return _result(code=0)
        if cmd[:3] == ["git", "rev-list", "--count"]:
            return _result(code=1, stderr="no upstream configured")
        return _result(code=0)

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(typer.Exit):
        system_cmd.update()

    assert ["git", "fetch", "--quiet"] in calls
    assert ["git", "rev-list", "--count", "HEAD..@{u}"] in calls


def test_update_handles_invalid_rev_list_count(monkeypatch):
    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            return _result(code=0)
        if cmd[:3] == ["git", "rev-list", "--count"]:
            return _result(code=0, stdout="not-a-number")
        return _result(code=0)

    monkeypatch.setattr("subprocess.run", fake_run)

    with pytest.raises(typer.Exit):
        system_cmd.update()


def test_update_returns_when_already_up_to_date(monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[:2] == ["git", "fetch"]:
            return _result(code=0)
        if cmd[:3] == ["git", "rev-list", "--count"]:
            return _result(code=0, stdout="0")
        return _result(code=0)

    monkeypatch.setattr("subprocess.run", fake_run)

    system_cmd.update()

    assert ["git", "pull", "--ff-only"] not in calls
