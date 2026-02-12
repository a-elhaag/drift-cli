# Contributing

Thank you for your interest in contributing! :tada:

## Code of Conduct

Be respectful, inclusive, and constructive.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/a-elhaag/drift-cli/issues) first
2. Include:
   - Drift version (`drift version`)
   - OS and shell version
   - Steps to reproduce
   - Expected vs actual behavior
   - Output from `drift doctor`

### Suggesting Features

Open an issue with:

- Clear use case
- Example usage
- Why it's useful

### Pull Requests

1. **Fork and clone** the repository
2. **Create a branch**: `git checkout -b feature/my-feature`
3. **Make changes** following our code style
4. **Add tests** for new functionality
5. **Run tests**: `make test`
6. **Format code**: `make format`
7. **Commit** with [conventional commits](https://www.conventionalcommits.org/)
8. **Push** and create a PR

## Code Style

- **Ruff** for linting and formatting
- **PEP 8** guidelines
- **Type hints** where appropriate
- **Docstrings** for public functions

## Commit Messages

```
feat: add support for bash completion
fix: prevent crash when Ollama is offline
docs: update installation instructions
test: add tests for history manager
refactor: simplify safety checker logic
```

## Areas for Contribution

### High Priority

- :red_circle: Linux support (installer and compatibility)
- :red_circle: Bash integration (in addition to ZSH)
- :red_circle: Improved error messages
- :red_circle: More comprehensive tests

### Medium Priority

- :yellow_circle: Additional model support
- :yellow_circle: Command aliasing
- :yellow_circle: Workspace-specific configurations

### Nice to Have

- :green_circle: Fish shell support
- :green_circle: Syntax highlighting for previews
- :green_circle: Interactive selection mode
