"""Tests for models."""

import pytest
from pydantic import ValidationError

from drift_cli.models import Command, Plan, RiskLevel


def test_command_model():
    """Test Command model validation."""
    cmd = Command(
        command="ls -la",
        description="List files",
        dry_run="ls -la --dry-run",
    )
    assert cmd.command == "ls -la"
    assert cmd.description == "List files"
    assert cmd.dry_run == "ls -la --dry-run"


def test_plan_model():
    """Test Plan model validation."""
    plan = Plan(
        summary="List files in current directory",
        risk=RiskLevel.LOW,
        commands=[
            Command(command="ls -la", description="List all files")
        ],
        explanation="This will list all files including hidden ones",
    )
    assert plan.summary == "List files in current directory"
    assert plan.risk == RiskLevel.LOW
    assert len(plan.commands) == 1


def test_plan_validation_error():
    """Test that Plan requires all fields."""
    with pytest.raises(ValidationError):
        Plan(
            summary="Test",
            # Missing required fields
        )


def test_risk_levels():
    """Test RiskLevel enum."""
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.MEDIUM.value == "medium"
    assert RiskLevel.HIGH.value == "high"
