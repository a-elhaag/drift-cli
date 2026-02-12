from drift_cli.core.safety import SafetyChecker
from drift_cli.models import RiskLevel


def test_blocks_destructive_commands():
    blocked, reason = SafetyChecker.is_blocked("rm -rf /")
    assert blocked is True
    assert "dangerous pattern" in reason


def test_assess_risk_levels():
    assert SafetyChecker.assess_risk("ls -la") == RiskLevel.LOW
    assert SafetyChecker.assess_risk("pip install requests") == RiskLevel.MEDIUM
    assert SafetyChecker.assess_risk("sudo rm -rf /tmp/foo") == RiskLevel.HIGH


def test_validate_commands_emits_warnings():
    all_safe, warnings = SafetyChecker.validate_commands(["ls", "git push"])
    assert all_safe is True
    assert any("MEDIUM RISK" in warning for warning in warnings)
