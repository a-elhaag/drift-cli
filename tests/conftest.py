from pathlib import Path
from typing import Optional

import pytest

from drift_cli.models import Command, Plan, RiskLevel


@pytest.fixture
def fake_home(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: home)
    return home


@pytest.fixture
def make_plan():
    def _make_plan(
        command: str = "echo ok",
        risk: RiskLevel = RiskLevel.LOW,
        dry_run: Optional[str] = None,
        affected_files: Optional[list[str]] = None,
    ) -> Plan:
        return Plan(
            summary="test plan",
            risk=risk,
            commands=[
                Command(
                    command=command,
                    description="test command",
                    dry_run=dry_run,
                )
            ],
            explanation="test explanation",
            affected_files=affected_files,
            clarification_needed=None,
        )

    return _make_plan
