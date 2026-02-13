# Memory System

Drift learns your preferences over time and adapts its suggestions.

## How It Works

Every time you use Drift, it observes:

- **Tools you prefer** — Do you use `rg` instead of `grep`? `fd` instead of `find`?
- **Risk tolerance** — Do you usually confirm HIGH-risk commands or cancel?
- **Common workflows** — What do you search for? What kind of projects do you work on?
- **Project context** — Different preferences per project directory

This data is stored locally in `~/.drift/` and **never leaves your machine**.

## Commands

### View Learned Preferences

```bash
drift memory show
```

Shows your tool preferences, risk patterns, and workflow insights.

### Usage Statistics

```bash
drift memory stats
```

Reports totals for queries, executions, and success rate and shows the risk distribution of executed plans so you can align Drift's default behavior with your comfort level.

### Personalized Insights

```bash
drift memory insights
```

Displays the exact prompt context sent to the LLM, surfaces pattern-based suggestions, and highlights learning opportunities from recent command history.

### Reset Everything

```bash
drift memory reset
```

!!! note
This permanently deletes all learned preferences. Drift starts fresh.

Add `--yes` to skip the confirmation prompt if you are scripting a reset.

### Export / Import

```bash
# Backup your preferences
drift memory export drift-memory.json

# Restore on another machine
drift memory import drift-memory.json
drift memory import drift-memory.json --merge
```

`--merge` combines exported preferences with your existing data (favorite tools, avoided patterns, and workflows are unioned instead of replaced).

### View Projects

```bash
drift memory projects
```

Lists all project directories where Drift has observed your patterns.

## What Gets Stored

| Data             | Example                          | Purpose                 |
| ---------------- | -------------------------------- | ----------------------- |
| Tool preferences | `grep → rg`                      | Suggest preferred tools |
| Shell patterns   | Prefers `find -exec` over piping | Match your style        |
| Risk decisions   | Usually accepts MEDIUM risk      | Adjust warnings         |
| Project types    | Python, Node.js                  | Context-aware defaults  |
| Common queries   | "find large files"               | Faster suggestions      |

## Privacy

- Memory is stored in `~/.drift/memory.json`, `~/.drift/context.json`, and `~/.drift/projects/*.json`
- Data is **never** sent to any remote server
- You can inspect, edit, or delete the files directly
- `drift memory reset` clears everything
