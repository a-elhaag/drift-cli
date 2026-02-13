# Drift CLI

A terminal-native, safety-first AI assistant that integrates directly into your shell. Powered by local LLMs via Ollama — no cloud dependency, full privacy.

Docs: https://a-elhaag.github.io/drift-cli/

## Features

- **Natural Language to Shell**: Press `Ctrl+Space` to translate English into executable commands with rich previews.
- **Safety First**: Automatic blocklists, risk scoring, dry-run defaults, and confirmation prompts before every execution.
- **Local-First**: Runs entirely on your machine via Ollama (no API keys, no cloud tracking).
- **Smart Workflows**: Plan → Preview → Confirm → Execute → Explain → Undo keeps every run recoverable.
- **Slash Commands**: `/git`, `/commit`, `/status`, `/push`, `/pull`, `/find`, `/recent`, `/large`, `/tree`, `/fix`, `/clean`, `/deps`, `/port`, `/test`, `/build`, `/dev`, `/lint`, `/help`, `/tips` — all dispatched from the terminal prompt with contextual awareness.
- **Memory System**: Tracks your preferred tools, risk tolerance, and workflows via `drift memory show`, `drift memory stats`, `drift memory insights`, and portable export/import utilities.
- **System & Maintenance**: `drift doctor`, `drift config`, `drift setup`, `drift update`, `drift uninstall`, and `drift version` keep your environment healthy and configurable.
- **ZSH Integration**: Seamless hotkey binding for Ctrl+Space and slash command interception.

## Quick Start

```bash
# Install Drift CLI
git clone https://github.com/a-elhaag/drift-cli.git
cd drift-cli
pip install -e .

# Just run it — Drift auto-installs Ollama & pulls the model on first use
drift suggest find all python files modified today
drift explain tar -czf archive.tar.gz src/
drift doctor
```

> **Zero setup**: Drift automatically installs Ollama, starts the server, and pulls the model on first run. Configure via `~/.drift/config.json`.

## Commands

### Core AI

| Command                   | Description                                                                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `drift suggest <query>`   | Natural language → shell with `--dry-run`, `--execute`, `--verbose`, `--no-memory` flags and slash-command support (`drift /help` for a live catalog). |
| `drift find <query>`      | Safe, read-only file and content search powered by the same reasoning stack.                                                                           |
| `drift explain <command>` | Ask the LLM to explain what any shell command does before you run it.                                                                                  |

### Workflow & history

| Command                                        | Description                                                                 |
| ---------------------------------------------- | --------------------------------------------------------------------------- |
| `drift history [--limit N]`                    | Browse recent queries, outcomes, and snapshots.                             |
| `drift again`                                  | Re-run the last Drift query (great for retries after tweaking options).     |
| `drift undo`                                   | Restore files from the most recent snapshot (requires an executed command). |
| `drift cleanup [--keep N] [--days D] [--auto]` | Delete old snapshots to free space while keeping the newest backups.        |

### System & maintenance

| Command           | Description                                                                                                                       |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `drift doctor`    | Verifies Ollama installation, server, and model availability (auto-install/start/pull if enabled).                                |
| `drift config`    | Interactively tune settings (`model`, `temperature`, `auto_install_ollama`, `auto_snapshot`, idle shutdown, etc.).                |
| `drift setup`     | Re-run the first-time wizard to reset defaults and bootstrapping.                                                                 |
| `drift update`    | Fetch the latest commits, reinstall via `pip install -e .`, and report the new version (works when Drift was installed from git). |
| `drift uninstall` | Remove `~/.drift`, optionally uninstall Ollama, and remind you to `pip uninstall drift-cli`.                                      |
| `drift version`   | Print the installed Drift CLI version.                                                                                            |

### Memory & personalization

| Command                                | Description                                                                                                         |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `drift memory show`                    | See your learned preferences, workflows, and current context.                                                       |
| `drift memory stats`                   | Usage totals plus risk distribution for executed plans.                                                             |
| `drift memory insights`                | Reveal the context Drift sends to Ollama, plus pattern-based suggestions and learning opportunities.                |
| `drift memory reset [--yes]`           | Wipe learned preferences while keeping the raw history.                                                             |
| `drift memory export <file>`           | Save your preferences/patterns to a JSON file for backup or sharing.                                                |
| `drift memory import <file> [--merge]` | Restore preferences; `--merge` unionizes favorite tools, avoided patterns, and workflows instead of replacing them. |
| `drift memory projects`                | List every project-specific preference file under `~/.drift/projects/`.                                             |

## Slash Commands

Slash commands are triggered by typing `/`-prefixed queries (requires ZSH integration). Drift intercepts the command, gathers context (git status, preferred tools, project type), and generates a safe plan via the slash registry.

| Category | Commands                                       |
| -------- | ---------------------------------------------- |
| Git      | `/git`, `/commit`, `/status`, `/push`, `/pull` |
| Files    | `/find`, `/recent`, `/large`, `/tree`          |
| System   | `/fix`, `/clean`, `/deps`, `/port`             |
| Workflow | `/test`, `/build`, `/dev`, `/lint`             |
| Meta     | `/help`, `/tips`                               |

Use `/help` for the live catalog, and `/tips` for personalized workflow suggestions driven by your history. All slashes honor Drift's safety engine, including the plan preview, risk badges, and confirmation prompts.

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

## System Requirements

| Requirement | Minimum                   | Required    | Notes                                                    |
| ----------- | ------------------------- | ----------- | -------------------------------------------------------- |
| OS          | macOS 12+ or modern Linux | Yes         | Windows is not supported yet                             |
| Python      | 3.9+                      | Yes         | Check with `python3 --version`                           |
| Ollama      | Latest                    | Yes         | Drift can auto-install/start/pull model                  |
| Shell       | Any shell for CLI         | Yes         | ZSH is only required for `Ctrl+Space` hotkey integration |
| Git         | Recent                    | Recommended | Needed for update workflow and project-aware context     |

Install behavior:

- `pip install -e .` installs only normal runtime dependencies.
- Dev/test/docs tooling is not installed unless you explicitly use extras (`.[dev,test]`) or install doc tooling manually.

## Development

```bash
# Install in development mode
pip install -e ".[dev,test]"

# Format code
make format

# Lint
make lint

# Run tests
make test

# Run full verification
make check
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
  "auto_snapshot": true,
  "auto_stop_ollama_when_idle": false,
  "ollama_idle_minutes": 30
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
