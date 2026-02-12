# Configuration

Drift stores its configuration at `~/.drift/config.json`.

## Default Configuration

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

## Settings Reference

| Setting                       | Default                  | Description                                                          |
| ----------------------------- | ------------------------ | -------------------------------------------------------------------- |
| `model`                       | `qwen2.5-coder:1.5b`     | Ollama model to use for inference                                    |
| `ollama_url`                  | `http://localhost:11434` | Ollama server URL                                                    |
| `temperature`                 | `0.1`                    | LLM temperature (lower = more deterministic)                         |
| `top_p`                       | `0.9`                    | Nucleus sampling parameter                                           |
| `max_history`                 | `100`                    | Maximum history entries before rotation                              |
| `auto_snapshot`               | `true`                   | Automatically create snapshots before file modifications             |
| `auto_stop_ollama_when_idle` | `false`                  | Stop Ollama automatically after inactivity (only when Drift started) |
| `ollama_idle_minutes`         | `30`                     | Idle duration before auto-stop                                       |

## Environment Variables

Override settings per-session without editing config:

| Variable                   | Description                           | Example                                  |
| -------------------------- | ------------------------------------- | ---------------------------------------- |
| `DRIFT_DRY_RUN=1`          | Force dry-run mode globally           | `export DRIFT_DRY_RUN=1`                 |
| `DRIFT_EXECUTOR=mock`      | Use mock executor (no real execution) | `export DRIFT_EXECUTOR=mock`             |
| `DRIFT_SANDBOX_ROOT=/path` | Restrict execution to a directory     | `export DRIFT_SANDBOX_ROOT=/tmp/sandbox` |
| `DRIFT_MODEL=model:tag`    | Override the LLM model                | `export DRIFT_MODEL=codellama:7b`        |

## Changing the Model

```bash
# Use a larger model for better suggestions
drift suggest "complex task"
# Override per-command:
DRIFT_MODEL=qwen2.5-coder:7b drift suggest "complex task"
```

Or edit `~/.drift/config.json`:

```json
{
  "model": "qwen2.5-coder:7b"
}
```

## File Locations

| Path                     | Purpose                       |
| ------------------------ | ----------------------------- |
| `~/.drift/config.json`   | User configuration            |
| `~/.drift/history.jsonl` | Command history (append-only) |
| `~/.drift/snapshots/`    | File snapshots for undo       |
| `~/.drift/drift.zsh`     | ZSH integration script        |
| `~/.drift/memory.json`   | Global learned preferences    |
| `~/.drift/context.json`  | Session/context metadata      |
| `~/.drift/projects/`     | Project-specific preferences  |
