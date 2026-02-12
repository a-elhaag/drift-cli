# Command Reference

## Core Commands

### `drift suggest`

Convert natural language to shell commands.

```bash
drift suggest <query> [--dry-run]
```

| Flag        | Description                     |
| ----------- | ------------------------------- |
| `--dry-run` | Show the plan without executing |

**Examples:**

```bash
drift suggest find all files larger than 100MB
drift suggest compress all .log files into an archive --dry-run
drift suggest set up a Python virtual environment
```

---

### `drift find`

Smart, read-only file and content search. Always safe — never modifies anything.

```bash
drift find <query>
```

**Examples:**

```bash
drift find all TODO comments in Python files
drift find configuration files
drift find largest files in this project
```

---

### `drift explain`

Get a detailed breakdown of any shell command.

```bash
drift explain <command>
```

**Examples:**

```bash
drift explain tar -czf archive.tar.gz src/
drift explain find . -name '*.py' -exec grep -l 'import os' {} +
drift explain awk '{print $1}' /var/log/syslog | sort | uniq -c | sort -rn
```

---

### `drift history`

View past Drift operations with timestamps, queries, and outcomes.

```bash
drift history [--limit N]
```

---

### `drift again`

Re-run the last Drift command.

```bash
drift again
```

---

### `drift undo`

Restore files from the most recent snapshot. Only works if the last command modified files and `auto_snapshot` is enabled.

```bash
drift undo
```

---

### `drift cleanup`

Remove old snapshots to free disk space.

```bash
drift cleanup [--days N]
```

---

### `drift doctor`

Run diagnostics to verify your setup.

```bash
drift doctor
```

Checks:

- Ollama is running and accessible
- `~/.drift/` directory exists
- Models are available
- ZSH integration status

---

### `drift version`

Show the installed version.

```bash
drift version
```

## Memory Commands

### `drift memory show`

Display what Drift has learned about your preferences.

```bash
drift memory show
```

### `drift memory stats`

Show usage statistics.

```bash
drift memory stats
```

### `drift memory reset`

Clear all learned preferences.

```bash
drift memory reset
```

### `drift memory export` / `drift memory import`

Export or import memory data for backup or transfer.

```bash
drift memory export my-prefs.json
drift memory import my-prefs.json
```

### `drift memory projects`

List projects Drift has learned about.

```bash
drift memory projects
```
