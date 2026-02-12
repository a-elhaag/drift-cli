# Drift CLI

A terminal-native, safety-first AI assistant that integrates directly into your shell. Powered by local LLMs via Ollama — no cloud dependency, full privacy.

## Features

- **Natural Language to Shell**: Press `Ctrl+Space` to transform natural language into safe, executable commands
- **Safety First**: Dry-run previews, risk scoring, blocklist validation, and confirmation prompts
- **Local-First**: Runs entirely on your machine using Ollama (no API keys, no cloud)
- **Smart Workflows**: Plan → Preview → Confirm → Execute → Explain → Undo
- **Slash Commands**: Quick context-aware actions (`/git`, `/commit`, `/find`, `/test`, etc.)
- **Memory System**: Learns your preferences and adapts suggestions over time
- **ZSH Integration**: Seamless hotkey binding for instant access

## Quick Start

```bash
# Install Drift CLI
git clone https://github.com/a-elhaag/drift-cli.git
cd drift-cli
pip install -e .

# Just run it — Drift auto-installs Ollama & pulls the model on first use
drift suggest "find all python files modified today"
drift explain "tar -czf archive.tar.gz src/"
drift doctor
```

> **Zero setup**: Drift automatically installs Ollama, starts the server, and pulls the model on first run. Configure via `~/.drift/config.json`.

## Commands

| Command                     | Description                           |
| --------------------------- | ------------------------------------- |
| `drift suggest "<query>"`   | Get AI-powered command suggestions    |
| `drift find "<query>"`      | Smart file and content search         |
| `drift explain "<command>"` | Understand what a command does        |
| `drift history`             | View your Drift command history       |
| `drift again`               | Re-run the last Drift command         |
| `drift undo`                | Restore files from the last operation |
| `drift cleanup`             | Remove old snapshots to free space    |
| `drift doctor`              | Diagnose common terminal issues       |
| `drift memory show`         | See what Drift has learned about you  |
| `drift memory stats`        | Usage statistics                      |
| `drift memory reset`        | Reset learned preferences             |
| `drift version`             | Show version                          |

## Slash Commands

Type a slash command in your terminal and press Enter:

| Command           | Description                                   |
| ----------------- | --------------------------------------------- |
| `/git`            | Suggest next git action based on repo status  |
| `/commit`         | Smart commit with AI-generated message        |
| `/find <pattern>` | Quick file/content search                     |
| `/test`           | Run project tests (auto-detects project type) |
| `/build`          | Build the project                             |
| `/clean`          | Clean project artifacts safely                |
| `/fix`            | Suggest fixes for recent errors               |
| `/help`           | Show all available slash commands             |

## Safe Execution

Drift provides multiple layers of safety to prevent accidental damage:

### Environment Variables

| Variable                   | Description                         | Example                                  |
| -------------------------- | ----------------------------------- | ---------------------------------------- |
| `DRIFT_DRY_RUN=1`          | Force dry-run mode (never executes) | `export DRIFT_DRY_RUN=1`                 |
| `DRIFT_EXECUTOR=mock`      | Use mock executor (logs only)       | `export DRIFT_EXECUTOR=mock`             |
| `DRIFT_SANDBOX_ROOT=/path` | Restrict execution to a directory   | `export DRIFT_SANDBOX_ROOT=/tmp/sandbox` |
| `DRIFT_MODEL=model:tag`    | Override the default LLM model      | `export DRIFT_MODEL=codellama:7b`        |

### Testing in Isolation

```bash
# Option 1: Dry-run mode (safest — see what would happen without executing)
drift suggest "delete all log files" --dry-run

# Option 2: Mock executor (commands are logged but never run)
DRIFT_EXECUTOR=mock drift suggest "reorganize my project"

# Option 3: Sandbox directory (commands only run inside a safe directory)
mkdir /tmp/drift-sandbox
DRIFT_SANDBOX_ROOT=/tmp/drift-sandbox drift suggest "create project structure"

# Option 4: Full isolation with Docker
# Set DRIFT_EXECUTOR=docker to run commands inside a container
```

### Programmatic Testing

```python
from drift_cli.core.executor_base import get_executor

# Mock executor — nothing is ever executed
executor = get_executor("mock")
result = executor.execute("rm -rf /")  # Safely logged, never runs
print(result.stdout)  # "[MOCK] Would execute: rm -rf /"

# Sandbox executor — runs in an isolated temporary directory
import tempfile
from pathlib import Path
sandbox = Path(tempfile.mkdtemp())
executor = get_executor("local", sandbox)
executor.execute("touch test.txt")  # Only creates file inside sandbox
```

## Requirements

- macOS (Linux support planned)
- Python 3.9+
- [Ollama](https://ollama.com) (auto-installed by installer)

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
make test

# Lint
make lint

# Format code
make format
```

## Configuration

Copy `config.example.json` to `~/.drift/config.json` and customize:

```json
{
  "model": "qwen2.5-coder:1.5b",
  "ollama_url": "http://localhost:11434",
  "temperature": 0.1,
  "top_p": 0.9,
  "max_history": 100,
  "auto_snapshot": true
}
```

## Architecture

```
drift_cli/
├── cli.py              # Main CLI (Typer app, all commands)
├── models.py           # Pydantic data models (Plan, Command, RiskLevel)
├── core/
│   ├── config.py       # Configuration management
│   ├── executor.py     # Command execution with safety checks
│   ├── executor_base.py # Executor interface (Mock, Local, Docker)
│   ├── history.py      # History & snapshot management
│   ├── memory.py       # User preference learning
│   ├── ollama.py       # Ollama LLM client
│   ├── safety.py       # Safety validation & risk scoring
│   └── slash_commands.py # Slash command system
├── commands/
│   └── memory_cmd.py   # Memory subcommands
└── ui/
    ├── display.py      # Rich terminal UI components
    └── progress.py     # Progress spinners & indicators
```

## License

MIT
