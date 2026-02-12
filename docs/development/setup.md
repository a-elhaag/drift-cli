# Development Setup

## Prerequisites

- Python 3.9+
- Ollama (for integration testing)
- Git

## Clone & Install

```bash
git clone https://github.com/a-elhaag/drift-cli.git
cd drift-cli

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode with dev + test dependencies
pip install -e ".[dev,test]"
```

## Project Structure

```
drift-cli/
├── drift_cli/              # Main package
│   ├── cli.py              # CLI entry point (Typer)
│   ├── models.py           # Pydantic models
│   ├── core/
│   │   ├── config.py       # Configuration management
│   │   ├── executor.py     # Command execution + safety
│   │   ├── executor_base.py # Mock/Local/Docker executors
│   │   ├── history.py      # History & snapshots
│   │   ├── memory.py       # User preference learning
│   │   ├── ollama.py       # Ollama API client
│   │   ├── safety.py       # Safety validation & risk scoring
│   │   └── slash_commands.py # Slash command registry
│   ├── commands/
│   │   └── memory_cmd.py   # Memory subcommands
│   └── ui/
│       ├── display.py      # Rich terminal UI
│       └── progress.py     # Progress spinners
├── tests/
│   ├── conftest.py         # Shared fixtures
│   ├── test_auto_setup.py  # Auto-setup behavior tests
│   ├── test_executor.py    # Executor behavior tests
│   ├── test_history.py     # History and snapshot tests
│   ├── test_memory.py      # Memory merge/context tests
│   ├── test_safety.py      # Safety engine tests
│   ├── test_slash_commands.py  # Slash command tests
│   └── test_system_update.py   # Update command failure-mode tests
├── pyproject.toml
├── Makefile
└── mkdocs.yml
```

## Running Tests

```bash
# All tests
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=drift_cli --cov-report=html

# Specific file
pytest tests/test_safety.py -v
```

## Linting & Formatting

```bash
# Check
ruff check drift_cli tests

# Format
ruff format drift_cli tests

# Or use Make
make lint
make format
```

## Makefile Targets

```bash
make test        # Run tests
make lint        # Check linting
make format      # Format code
make dev         # Install in dev mode
make clean       # Remove build artifacts
```

## Adding a New Command

1. Add the command to `drift_cli/cli.py`:

   ```python
   @app.command()
   def mycommand(
       arg: str = typer.Argument(..., help="Description"),
   ):
       """Brief description."""
       # implementation
   ```

2. Add tests in `tests/`
3. Update docs in `docs/guide/commands.md`

## Modifying Safety Rules

1. Edit `drift_cli/core/safety.py`
2. Add regex pattern to `HARD_BLOCKLIST`, `HIGH_RISK_PATTERNS`, or `MEDIUM_RISK_PATTERNS`
3. Add corresponding test in `tests/test_safety.py`

## Testing Without Ollama

You can run all tests without Ollama — the test suite uses mocks:

```bash
pytest  # Works without Ollama running
```

For manual CLI testing without Ollama, use mock executor:

```bash
DRIFT_EXECUTOR=mock drift suggest "anything"
```

## Building Docs Locally

```bash
pip install mkdocs-material
mkdocs serve   # Preview at http://localhost:8000
mkdocs build   # Build static site
```
