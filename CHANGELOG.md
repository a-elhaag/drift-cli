# Changelog

All notable changes to Drift CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-09

### Added
- Initial release of Drift CLI
- Natural language to shell command conversion
- Safety-first execution with dry-run previews
- Risk level assessment (low/medium/high)
- Command history with JSONL storage
- Snapshot-based undo functionality
- ZSH integration with Ctrl+Space hotkey
- Core commands:
  - `drift suggest` - Get AI-powered command suggestions
  - `drift find` - Smart file and content search
  - `drift explain` - Explain shell commands
  - `drift history` - View command history
  - `drift again` - Re-run last command
  - `drift undo` - Restore files from last operation
  - `drift doctor` - System diagnostics
- Local-first with Ollama (qwen2.5-coder:1.5b)
- Rich-based terminal UI
- Automated installer for macOS
- Comprehensive safety blocklist
- Configuration file support

### Security
- Hard blocklist for dangerous commands (rm -rf /, sudo rm -rf, etc.)
- Risk-based confirmation prompts
- File snapshot system for safe rollback
- No cloud dependency - fully local execution
