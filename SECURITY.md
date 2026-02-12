# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Philosophy

Drift CLI is designed with a **safety-first** approach:

1. **Local-First**: All processing happens on your machine. No data is sent to cloud services.
2. **Explicit Confirmation**: Destructive operations require user confirmation.
3. **Hard Blocklist**: Dangerous commands are blocked and never executed.
4. **Risk Assessment**: Every command is evaluated for potential harm.
5. **Snapshot System**: Files are backed up before modification.

## Security Features

### Command Blocklist

The following patterns are **hard-blocked** and will never execute:

- `rm -rf /` and variants
- `sudo rm -rf` operations on root or system directories
- Disk formatting commands (`mkfs`, `diskutil eraseDisk`)
- Piping curl/wget to shell (`curl ... | sh`)
- Device file operations that could corrupt data
- Fork bombs and similar malicious patterns

See `drift_cli/core/safety.py` for the complete list.

### Risk Levels

Commands are classified into three risk levels:

- **LOW**: Read-only operations (safe)
- **MEDIUM**: File modifications, installations
- **HIGH**: System-level changes, destructive operations

High-risk operations require typing "YES" explicitly.

### Snapshot System

Before executing commands that modify files:

1. A snapshot is created in `~/.drift/snapshots/`
2. Original files are backed up
3. Changes can be rolled back with `drift undo`

## Reporting a Vulnerability

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email security@[your-domain].com with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We aim to respond within 48 hours.

## Security Best Practices for Users

### Do:
- ✅ Review commands before confirming
- ✅ Use `--dry-run` flag for risky operations
- ✅ Keep Ollama and Drift CLI updated
- ✅ Verify the installer script before running

### Don't:
- ❌ Disable safety checks
- ❌ Run Drift with sudo/root privileges
- ❌ Ignore high-risk warnings
- ❌ Execute commands you don't understand

## Known Limitations

1. **Snapshot System**: Only backs up files that the LLM identifies as affected. Hidden side effects may not be captured.
2. **Safety Blocklist**: Cannot catch all dangerous operations. Use common sense.
3. **LLM Limitations**: The model may occasionally suggest suboptimal or incorrect commands. Always review before executing.

## Threat Model

### In Scope:
- Command injection vulnerabilities
- Bypass of safety blocklist
- Privilege escalation
- Data loss through incorrect operations

### Out of Scope:
- Social engineering attacks
- Physical access to the machine
- Vulnerabilities in Ollama itself
- OS-level vulnerabilities

## Updates and Patches

Security updates will be released as soon as possible and announced:
- In the CHANGELOG.md
- Via GitHub releases
- In the project README

## Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities.
