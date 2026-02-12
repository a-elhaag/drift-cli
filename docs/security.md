# Security

## Security Philosophy

Drift CLI is designed with a **safety-first** approach:

1. **Local-First** — All processing happens on your machine. No data is sent to cloud services.
2. **Explicit Confirmation** — Destructive operations require user confirmation.
3. **Hard Blocklist** — Dangerous commands are blocked and never executed.
4. **Risk Assessment** — Every command is evaluated for potential harm.
5. **Snapshot System** — Files are backed up before modification.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Command Blocklist

The following patterns are **hard-blocked** and will never execute:

- `rm -rf /` and variants
- `sudo rm -rf` on root or system directories
- Disk formatting commands (`mkfs`, `diskutil eraseDisk`)
- Piping curl/wget to shell (`curl ... | sh`)
- Device file operations that could corrupt data
- Fork bombs and similar malicious patterns
- Crypto mining commands
- Reverse shells and network exfiltration
- Base64-obfuscated command execution

See [Safety Engine](architecture/safety.md) for the complete list.

## Risk Levels

| Level                      | When                         | Confirmation    |
| -------------------------- | ---------------------------- | --------------- |
| **LOW** :green_circle:     | Read-only operations         | `y/N`           |
| **MEDIUM** :yellow_circle: | File modifications, installs | `y/N`           |
| **HIGH** :red_circle:      | System changes, deletions    | Must type `YES` |

## Snapshot System

Before executing commands that modify files:

1. A snapshot is created in `~/.drift/snapshots/`
2. Original files are backed up
3. Changes can be rolled back with `drift undo`

## Threat Model

**In Scope:**

- Command injection vulnerabilities
- Bypass of safety blocklist
- Privilege escalation
- Data loss through incorrect operations

**Mitigations:**

- LLM hallucinations → Pydantic validation + blocklist + user confirmation
- Blocklist bypass → Regex patterns + user review
- Snapshot corruption → Metadata validation + path traversal protection

## Reporting a Vulnerability

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Contact the maintainers privately
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Best Practices

### Do

- :white_check_mark: Review commands before confirming
- :white_check_mark: Use `--dry-run` for risky operations
- :white_check_mark: Keep Ollama and Drift updated
- :white_check_mark: Verify generated commands make sense

### Don't

- :x: Run Drift with sudo/root privileges
- :x: Ignore HIGH-risk warnings
- :x: Execute commands you don't understand
- :x: Disable safety checks

## Known Limitations

1. **Snapshot coverage** — Only backs up files the LLM identifies as affected. Hidden side effects may not be captured.
2. **Blocklist completeness** — Cannot catch every dangerous operation. Use common sense.
3. **LLM accuracy** — The model may occasionally suggest incorrect commands. Always review.
