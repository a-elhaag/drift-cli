"""Safety module for validating and scoring commands with improved patterns."""

import re
from typing import List, Tuple

from drift_cli.models import RiskLevel


class SafetyChecker:
    """Validates commands for safety and assigns risk levels."""

    # Commands that should NEVER be executed
    HARD_BLOCKLIST = [
        # Destructive root operations
        r"rm\s+-rf\s*/($|\s)",  # rm -rf /
        r"rm\s+-rf\s+/[a-z]+",  # rm -rf /usr, /var, etc.
        r"rm\s+-rf\s+\*",
        r"sudo\s+rm\s+-rf",
        r"mkfs\.",
        r"dd\s+if=.*of=/dev/",
        r"dd\s+.*of=/dev/(sd|hd|nvme)",
        # Dangerous downloads and execution
        r"curl[^\|]*\|\s*(sh|bash|zsh|python|ruby|perl)",
        r"wget[^\|]*\|\s*(sh|bash|zsh|python|ruby|perl)",
        r"<\(curl",  # process substitution with curl
        r"<\(wget",
        # Fork bomb
        r":\(\)\{\s*:\|:&\s*\};:",
        # Disk operations
        r"diskutil\s+(eraseDisk|eraseVolume)",
        r"fdisk\s+",
        r"parted\s+",
        # Writing to raw devices
        r">\s*/dev/(sd|hd|nvme)",
        r"mv\s+.*\s+/dev/(sd|hd|nvme|null)",
        # Dangerous permissions
        r"chmod\s+(-R\s+)?777\s+/",
        r"chown\s+-R\s+.*\s+/",
        # Code execution
        r"python[23]?\s+-c\s+.*exec\s*\(",
        r"python[23]?\s+-c\s+.*eval\s*\(",
        r"perl\s+-e\s+",
        r"ruby\s+-e\s+",
        r"node\s+-e\s+",
        r"php\s+-r\s+",
        # Shell command injection patterns
        r"bash\s+-c\s+.*\$\(",  # Command substitution
        r"sh\s+-c\s+.*`",  # Backtick substitution
        r"eval\s+\$",  # eval with variable
        # Crypto miners and malware patterns
        r"xmrig",
        r"cryptonight",
        r"base64.*perl.*exec",
    ]

    # Patterns that indicate high risk
    HIGH_RISK_PATTERNS = [
        r"sudo\s+",
        r"rm\s+-r(f)?\s+",  # Recursive removal
        r"chmod\s+777",
        r"chmod\s+-R",
        r"chown\s+-R",
        r">/dev/",
        r"dd\s+",
        r"format\s+",
        r"kill\s+-9",
        r"pkill\s+",
        r"killall\s+",
        r"dscl\s+",  # Directory service command line
        r"launchctl\s+unload",
        r"systemctl\s+disable",
        r"git\s+push\s+(-f|--force)",
        r"git\s+reset\s+--hard",
        r"docker\s+system\s+prune\s+-a",
        r"npm\s+uninstall\s+-g",
        r"brew\s+uninstall",
    ]

    # Patterns that indicate medium risk
    MEDIUM_RISK_PATTERNS = [
        r"rm\s+",
        r"mv\s+",
        r"chmod\s+",
        r"chown\s+",
        r"git\s+push",
        r"git\s+commit\s+--amend",
        r"npm\s+install\s+-g",
        r"pip\s+install",
        r"brew\s+install",
        r"apt-get\s+install",
        r"yum\s+install",
        r"docker\s+run",
        r"docker\s+exec",
        r">\s*",  # Any file redirection
        r">>",  # Append redirection
    ]

    @classmethod
    def is_blocked(cls, command: str) -> Tuple[bool, str]:
        """
        Check if command matches hard blocklist.

        Returns:
            Tuple of (is_blocked, reason)
        """
        for pattern in cls.HARD_BLOCKLIST:
            if re.search(pattern, command, re.IGNORECASE):
                return True, f"Blocked: dangerous pattern detected ({pattern[:30]}...)"
        return False, ""

    @classmethod
    def assess_risk(cls, command: str) -> RiskLevel:
        """
        Assess the risk level of a command.

        Returns:
            RiskLevel enum value
        """
        # Check hard blocklist first
        if cls.is_blocked(command)[0]:
            return RiskLevel.HIGH

        # Check high risk patterns
        for pattern in cls.HIGH_RISK_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return RiskLevel.HIGH

        # Check medium risk patterns
        for pattern in cls.MEDIUM_RISK_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return RiskLevel.MEDIUM

        return RiskLevel.LOW

    @classmethod
    def validate_commands(cls, commands: List[str]) -> Tuple[bool, List[str]]:
        """
        Validate a list of commands.

        Returns:
            Tuple of (all_safe, list_of_warnings)
        """
        warnings = []
        all_safe = True

        for cmd in commands:
            blocked, reason = cls.is_blocked(cmd)
            if blocked:
                all_safe = False
                warnings.append(f"❌ BLOCKED: {cmd}\n   Reason: {reason}")
            else:
                risk = cls.assess_risk(cmd)
                if risk == RiskLevel.HIGH:
                    warnings.append(f"⚠️  HIGH RISK: {cmd}")
                elif risk == RiskLevel.MEDIUM:
                    warnings.append(f"⚡ MEDIUM RISK: {cmd}")

        return all_safe, warnings
