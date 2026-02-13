# Command Reference

## AI-powered core commands

### `drift suggest <query>`

Translate natural language into safe shell commands. Accepts a plain sentence or a slash command (start with `/`).

```bash
drift suggest "find all Python files modified today" --dry-run
drift suggest "/git"              # runs the git slash command
drift suggest "build the project" --execute
```

| Flag             | Description                                                     |
| ---------------- | --------------------------------------------------------------- |
| `-d`/`--dry-run` | Preview the plan but do not execute anything.                   |
| `-e`/`--execute` | Skip confirmation and run the plan immediately.                 |
| `-v`/`--verbose` | Show the plan plus a detailed explanation pane.                 |
| `--no-memory`    | Temporarily disable personalization and history-driven context. |

Use `drift /help` to see the latest slash command catalog (see [Slash commands](slash-commands.md)).

### `drift find <query>`

Smart, read-only file/content search driven by Drift's safety engine.

```bash
drift find "TODOs in Python"
drift find "*.md references to README"
```

It always runs in read-only mode, even if the LLM suggests `rm` or `mv`.

### `drift explain <command>`

Ask Drift to translate any shell command into plain English.

```bash
drift explain "tar -czf archive.tar.gz src/"
drift explain "rg TODO" --verbose
```

Provides contextual breakdowns so you can understand what you would be executing.

## History & workflow helpers

### `drift history [--limit N]`

Lists the last `N` queries, execution status, exit codes, and snapshots.

```bash
drift history --limit 20
```

### `drift again`

Re-runs the last Drift query. Useful after refining a plan or testing safety tweaks.

### `drift undo`

Restores files from the most recent snapshot. Drift prompts for confirmation and only allows undoing executed commands that captured a snapshot.

### `drift cleanup [--keep N] [--days D] [--auto]`

Deletes old snapshots to free disk space while keeping your most recent history.

```bash
drift cleanup --keep 30 --days 14   # keep the 30 newest snapshots, drop ones older than 14 days
drift cleanup --auto                 # skip the confirmation prompt
```

## System & setup commands

### `drift doctor`

Health-checks your environment:

- Verifies Ollama is installed and running (auto-installs or starts it when configured).
- Confirms the configured model is downloaded (auto-pulls if enabled).
- Reports the status of `~/.drift` and highlights missing requirements.

Use this after reinstalling or when Drift starts behaving unexpectedly.

### `drift config`

Interactively edits `~/.drift/config.json` without leaving the terminal.

Options include:

- Model override (default `qwen2.5-coder:1.5b` or whatever `DRIFT_MODEL` says)
- Ollama URL and idle behavior
- Numerical settings like `temperature`, `max_history`, `ollama_idle_minutes`
- Toggles for `auto_install_ollama`, `auto_start_ollama`, `auto_pull_model`, `auto_snapshot`, and `auto_stop_ollama_when_idle`

Each change is persisted instantly and reported with a confirmation banner.

### `drift setup`

Reruns the first-run wizard so you can reinitialize Ollama, models, and safe defaults.

### `drift update`

Automatically fetches the latest commit from `origin/main` (requires Drift was installed from the git clone). It:

1. Runs `git fetch` and `git pull --ff-only`.
2. Reinstalls the editable package via `python -m pip install -e .`.
3. Reports the new version.

If update fails (no upstream, diverged branch, or pip errors) Drift prints corrective actions and aborts cleanly.

### `drift uninstall`

Cleans up everything Drift owns:

- Prompted removal of `~/.drift` (config, history, snapshots)
- Optional uninstall of Ollama (platform-aware logic for macOS/Linux)
- Final reminder to run `pip uninstall drift-cli`.

### `drift version`

Outputs the currently installed Drift CLI version (sanity check for scripts).

## Memory & personalization commands

### `drift memory show`

Visualizes what Drift has learned about you (tools, risk tolerance, workflows, context, and current repo).

### `drift memory stats`

Shows aggregate usage telemetry:

- Total queries, commands executed, success rate
- Risk distribution for executed plans
- Highlights how Drift balances safety vs. execution

### `drift memory insights`

Explains what context is sent to the LLM, surface personalized suggestions, and shares opportunities detected in your recent history.

### `drift memory reset [--yes]`

Clears both preferences and context data (history is retained). Without `--yes` you get a confirmation prompt.

### `drift memory export <path>`

Dumps your learned preferences, patterns, and favorite tools into a JSON file with timestamps.

### `drift memory import <path> [--merge]`

Restores exported preferences. Use `--merge` to combine with existing data instead of overwriting everything.

### `drift memory projects`

Lists every project-specific preference file under `~/.drift/projects/`, along with last-updated timestamps and how many tools/patterns were captured.

Use the memory commands when you want deeper insight into Drift's personalization layer or to move preferences between machines.
