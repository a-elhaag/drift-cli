# Development Guide

## Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/drift-cli.git
cd drift-cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev,test]"

# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the default model
ollama pull qwen2.5-coder:1.5b
```

## Project Structure

```
drift-cli/
├── drift_cli/           # Main package
│   ├── core/           # Core functionality
│   │   ├── config.py   # Configuration management
│   │   ├── executor.py # Command execution
│   │   ├── history.py  # History and snapshots
│   │   ├── ollama.py   # Ollama API client
│   │   └── safety.py   # Safety checks
│   ├── ui/             # User interface
│   │   └── display.py  # Rich-based UI
│   ├── cli.py          # Main CLI application
│   └── models.py       # Pydantic models
├── tests/              # Pytest suite
├── drift.zsh           # ZSH integration
├── install.sh          # Installer script
└── pyproject.toml      # Project metadata
```

## Code Style

We use `ruff` for linting and formatting:

```bash
# Check code
ruff check drift_cli tests

# Format code
ruff format drift_cli tests
```

## Testing

```bash
# Run all tests
pytest -q

# Equivalent make target
make test
```

## Adding New Commands

1. Add command function to `drift_cli/cli.py`:

```python
@app.command()
def mycommand(arg: str = typer.Argument(..., help="Description")):
    """Command description."""
    # Implementation
```

2. Add the command to README.md
3. Update docs/guide/commands.md with new command

## Modifying Safety Rules

Edit `drift_cli/core/safety.py`:

- Add patterns to `HARD_BLOCKLIST` for commands that should never run
- Add to `HIGH_RISK_PATTERNS` or `MEDIUM_RISK_PATTERNS` for risk assessment

## Changing the System Prompt

The LLM system prompt is in `drift_cli/core/ollama.py` in the `_build_system_prompt()` method.

## Configuration

Users can customize Drift by editing `~/.drift/config.json`:

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

## Testing Ollama Integration

```python
from drift_cli.core.ollama import OllamaClient

client = OllamaClient()
if client.is_available():
    plan = client.get_plan("list all python files")
    print(plan)
```

## Release Process

1. Update version in `drift_cli/__init__.py`
2. Update CHANGELOG.md
3. Verify: `make check`
4. Build: `python -m build`
5. Tag release: `git tag v0.1.0`
6. Push: `git push --tags`
