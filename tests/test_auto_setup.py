from types import SimpleNamespace

import drift_cli.core.auto_setup as auto_setup


def test_install_ollama_macos_uses_consistent_archive_path(monkeypatch):
    monkeypatch.setattr(auto_setup.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(auto_setup.shutil, "which", lambda _: None)

    run_calls = []

    def fake_run(cmd, **kwargs):
        run_calls.append(cmd)
        if cmd[:3] == ["curl", "-fsSL", "-o"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if cmd[:2] == ["unzip", "-o"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        if cmd[:3] == ["test", "-d", "/Applications/Ollama.app"]:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(auto_setup.subprocess, "run", fake_run)

    assert auto_setup.install_ollama() is True

    curl_cmd = next(cmd for cmd in run_calls if cmd and cmd[0] == "curl")
    unzip_cmd = next(cmd for cmd in run_calls if cmd and cmd[0] == "unzip")

    assert curl_cmd[3] == "/tmp/Ollama-darwin.zip"
    assert unzip_cmd[2] == "/tmp/Ollama-darwin.zip"


def test_schedule_idle_shutdown_skips_when_disabled(monkeypatch, fake_home):
    popen_calls = []
    monkeypatch.setattr(auto_setup.subprocess, "Popen", lambda *a, **k: popen_calls.append((a, k)))

    auto_setup.schedule_idle_shutdown_if_needed(enabled=False, idle_minutes=10)
    assert popen_calls == []


def test_schedule_idle_shutdown_requires_drift_marker(monkeypatch, fake_home):
    popen_calls = []
    monkeypatch.setattr(auto_setup.subprocess, "Popen", lambda *a, **k: popen_calls.append((a, k)))

    auto_setup.schedule_idle_shutdown_if_needed(enabled=True, idle_minutes=10)
    assert popen_calls == []

    marker = fake_home / ".drift" / "ollama.started_by_drift"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("1")

    auto_setup.schedule_idle_shutdown_if_needed(enabled=True, idle_minutes=10)
    assert len(popen_calls) == 1
