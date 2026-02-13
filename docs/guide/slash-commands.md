# Slash Commands

Slash commands are quick, context-aware shortcuts that start with `/` and run inside your shell (ZSH integration required). You can type `/git`, `/find TODO`, `/lint`, etc., and Drift reroutes the query through the slash command handler to provide a focused suggestion without leaving your current workflow.

## How slash commands work

1. Type a slash command (e.g., `/git`) anywhere in your terminal and press Enter.
2. Drift intercepts the query and adds project context from your current directory, git status, and learned preferences.
3. The slash handler sends a tailored prompt to the local Ollama model.
4. Drift shows the generated plan, risk score, and executes only after you confirm.

`drift /help` prints a live catalog of all slash commands and their icons.

## Git commands (require a git repository)

| Command      | Description                                                                                                     |
| ------------ | --------------------------------------------------------------------------------------------------------------- |
| 🔀 `/git`    | Analyze the repo state and suggest the next logical git action, including staging helpers or rebase reminders.  |
| 📝 `/commit` | Reads staged changes and proposes a conventional commit message plus the git commands to run.                   |
| 📊 `/status` | Explains your git status output and suggests what to do next (stage files, pull, etc.).                         |
| ⬆️ `/push`   | Verifies there are commits to push and suggests a safe `git push` (with `--force-with-lease` only when needed). |
| ⬇️ `/pull`   | Pulls latest changes safely by checking for local edits, suggesting `stash` or rebase if required.              |

## File & discovery commands

| Command      | Description                                                                   |
| ------------ | ----------------------------------------------------------------------------- |
| 🔍 `/find`   | Finds files or content using `fd`, `rg`, or `find` while remaining read-only. |
| 🕐 `/recent` | Lists files modified in the last 24 hours, sorted by timestamp.               |
| 📦 `/large`  | Searches for large files (>10 MB) and reports their sizes.                    |
| 🌳 `/tree`   | Shows the directory tree (depth limited to 3 levels for brevity).             |

## System & diagnostics

| Command     | Description                                                                                                         |
| ----------- | ------------------------------------------------------------------------------------------------------------------- |
| 🔧 `/fix`   | Looks at recent errors and environment issues, then suggests explicit fixes (missing packages, permissions, etc.).  |
| 🧹 `/clean` | Identifies and removes project artifacts (`node_modules`, `__pycache__`, `.next`, etc.) in a safe, confirmable way. |
| 📚 `/deps`  | Scans dependencies for the detected project type and proposes update commands or checks.                            |
| 🔌 `/port`  | Reports what process is bound to a port (default dev ports if unspecified).                                         |

## Workflow shortcuts

| Command     | Description                                                                                                  |
| ----------- | ------------------------------------------------------------------------------------------------------------ |
| 🧪 `/test`  | Auto-detects the project type and runs the appropriate test command (`pytest`, `npm test`, `go test`, etc.). |
| 🔨 `/build` | Runs the build command for your stack (Python install, npm build, go build) and helps capture output.        |
| 🚀 `/dev`   | Starts the development server for the detected framework (uvicorn/flask, `npm run dev`, etc.).               |
| ✨ `/lint`  | Runs the linter/formatter for the detected stack and optionally suggests fixes.                              |

## Meta helpers

| Command    | Description                                                                                                |
| ---------- | ---------------------------------------------------------------------------------------------------------- |
| ❓ `/help` | Shows the live slash command catalog grouped by category.                                                  |
| 💡 `/tips` | Asks Drift for personalized workflow tips based on your history (alias ideas, shortcut suggestions, etc.). |

## Tips

- Slash commands automatically pull git context (branch, staged files, unpushed commits) when required.
- Drift remembers your favorite tools and can inject them into slash prompts (e.g., prefer `rg` over `grep`).
- If a command needs git and you're outside a repo, Drift tells you (`Not in a git repository`).
- Use `/help` to discover new commands as the registry evolves over time.

Slash commands keep Drift fast for repeatable tasks, but you still get the same safety pipeline (risk badges, dry-run preview, mandatory confirmation). Ultimately you stay in the shell and avoid juggling multiple tabs or prompts.
