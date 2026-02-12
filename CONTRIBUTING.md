# Contributing to Drift CLI

Thank you for your interest in contributing! 🎉

## Code of Conduct

This project follows `CODE_OF_CONDUCT.md`.
Be respectful, inclusive, and constructive. We're all here to make the terminal smarter and safer.

## How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Use the bug report template
3. Include:
   - Drift version (`drift version`)
   - OS and shell version
   - Steps to reproduce
   - Expected vs actual behavior
   - Output from `drift doctor`

### Suggesting Features

1. Check if it's already suggested
2. Open an issue with:
   - Clear use case
   - Example usage
   - Why it's useful
   - Potential implementation approach

### Pull Requests

1. **Fork and clone** the repository
2. **Create a branch**: `git checkout -b feature/my-feature`
3. **Make changes** following our code style
4. **Update documentation** if needed
5. **Format code**: `make format`
6. **Lint**: `make lint`
7. **Test**: `make test`
8. **Commit** with clear messages
9. **Push** and create a PR

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/drift-cli.git
cd drift-cli

# Install in development mode
make dev  # installs dev + test extras

# Check linting
make lint

# Format code
make format

# Run tests
make test
```

## Code Style

- Use **Ruff** for formatting and linting
- Follow **PEP 8** guidelines
- Use **type hints** where appropriate
- Write **docstrings** for public functions
- Keep functions **small and focused**

## Testing

All contributions should include automated test coverage when practical.
Test both success and failure cases.

### Running Tests

```bash
# Run tests
make test

# Lint + tests
make check
```

## Architecture Guidelines

### Adding a New Command

1. Add command function in `drift_cli/cli.py`
2. Use Typer decorators and type hints
3. Add safety checks if needed
4. Update help text and README

Example:

```python
@app.command()
def mycommand(
    arg: str = typer.Argument(..., help="Description"),
    flag: bool = typer.Option(False, "--flag", "-f", help="Flag help"),
):
    """Brief command description."""
    check_ollama()
    # Implementation
```

### Modifying Safety Rules

1. Update `drift_cli/core/safety.py`
2. Add patterns to appropriate list
3. Document in SECURITY.md

### Changing the LLM Prompt

1. Edit `_build_system_prompt()` in `drift_cli/core/ollama.py`
2. Test with various queries
3. Ensure JSON schema is clear
4. Add examples if needed

## Documentation

Update relevant docs:

- **README.md** - Main documentation
- **QUICKSTART.md** - User guide
- **DEVELOPMENT.md** - Developer guide
- **CHANGELOG.md** - Version changes
- **SECURITY.md** - Security implications

## Commit Messages

Use conventional commits:

```
feat: add support for bash completion
fix: prevent crash when Ollama is offline
docs: update installation instructions
test: add tests for history manager
refactor: simplify safety checker logic
```

## Areas for Contribution

### High Priority

- 🔴 Linux support (installer and compatibility)
- 🔴 Bash integration (in addition to ZSH)
- 🔴 Improved error messages
- 🔴 More comprehensive tests

### Medium Priority

- 🟡 Additional models support
- 🟡 Command aliasing
- 🟡 Workspace-specific configurations
- 🟡 Better dry-run previews

### Nice to Have

- 🟢 Fish shell support
- 🟢 Syntax highlighting for previews
- 🟢 Interactive selection mode
- 🟢 Export/import history

## Questions?

- Open a discussion on GitHub
- Tag issues with `question`
- Check existing issues and PRs

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in the README

---

Thank you for making Drift better! 🚀
