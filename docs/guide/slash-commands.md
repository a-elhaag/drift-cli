# Slash Commands

Slash commands are quick, context-aware shortcuts you can type directly in your terminal (requires ZSH integration).

## Available Commands

| Command           | Description                                              |
| ----------------- | -------------------------------------------------------- |
| `/git`            | Analyze repo status, suggest next git action             |
| `/commit`         | Generate conventional commit message from staged changes |
| `/find <pattern>` | Smart file and content search                            |
| `/test`           | Auto-detect project type, run tests                      |
| `/build`          | Build the project                                        |
| `/clean`          | Clean build artifacts safely                             |
| `/fix`            | Suggest fixes for recent errors                          |
| `/deploy`         | Deployment suggestions                                   |
| `/env`            | Show environment information                             |
| `/deps`           | Manage dependencies                                      |
| `/lint`           | Run linting                                              |
| `/format`         | Format code                                              |
| `/docker`         | Docker-related operations                                |
| `/logs`           | View and analyze logs                                    |
| `/perf`           | Performance analysis                                     |
| `/db`             | Database operations                                      |
| `/api`            | API-related commands                                     |
| `/help`           | Show all available slash commands                        |

## How They Work

1. Type a slash command in your terminal
2. Press `Enter`
3. Drift intercepts it via ZSH integration
4. Gathers context (git status, project type, directory contents)
5. Generates the appropriate command
6. Shows preview with risk assessment
7. Executes on confirmation

## Examples

### Git workflow

```bash
# Check what to do next in your repo
/git
# → Shows: "You have 3 modified files, 1 untracked. Suggest: git add -A && git commit"

# Auto-generate commit message
/commit
# → Reads staged diff, generates: "feat: add safety blocklist for Docker commands"
```

### Testing

```bash
/test
# In a Python project → runs: pytest
# In a Node.js project → runs: npm test
# In a Go project → runs: go test ./...
```

### Searching

```bash
/find TODO
# → Generates: grep -rn "TODO" --include="*.py" --include="*.js" .
```

## Requirements

Slash commands require ZSH integration to be set up. See [Installation → ZSH Integration](../getting-started/installation.md#zsh-integration-optional).
