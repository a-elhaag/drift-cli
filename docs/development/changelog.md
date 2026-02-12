# Changelog

All notable changes to Drift CLI are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). Adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-02-09

### Added

- Initial release of Drift CLI
- Natural language to shell command conversion via local LLM
- Safety-first execution with dry-run previews
- Risk level assessment (LOW / MEDIUM / HIGH)
- Hard blocklist with 60+ dangerous patterns
- Command history with JSONL storage
- Snapshot-based undo functionality
- ZSH integration with `Ctrl+Space` hotkey
- Core commands: `suggest`, `find`, `explain`, `history`, `again`, `undo`, `doctor`, `version`
- Memory system that learns user preferences
- 18 slash commands (`/git`, `/commit`, `/find`, `/test`, etc.)
- Mock, Sandbox, and Docker executor modes for safe testing
- Local-first with Ollama (`qwen2.5-coder:1.5b` default)
- Rich-based terminal UI with themed panels and risk badges
- Automated installer for macOS
- Configuration file support (`~/.drift/config.json`)

### Security

- Hard blocklist for dangerous commands (`rm -rf /`, `sudo rm -rf`, fork bombs, etc.)
- Risk-based confirmation prompts (type YES for HIGH risk)
- File snapshot system for safe rollback
- Input sanitization before LLM queries
- Path traversal protection in snapshot restore
- No cloud dependency — fully local execution
