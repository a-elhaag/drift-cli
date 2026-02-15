# Quick Start

After [installing Drift](installation.md), try these commands to get a feel for how it works.

## Your First Command

Just type a natural language query — Drift understands what you want:

```bash
drift what is the time now
```

or

```bash
drift find all python files modified today
```

Drift queries the local LLM, generates a plan, and shows you a preview:

```
╭─ Plan ──────────────────────────────────────────────────────╮
│  Summary: Find Python files modified today                   │
│  Risk: 🟢 LOW                                              │
│                                                              │
│  $ find . -type f -name '*.py' -mtime -1                   │
│    → Find .py files modified in the last day                │
╰──────────────────────────────────────────────────────────────╯
Execute? [y/N]:
```

Type `y` to run it, or `n` to cancel.

## Safe Preview with Dry-Run

Not sure you trust it yet? Use `--dry-run`:

```bash
drift reorganize my project --dry-run
```

This shows the plan but **never executes anything** — no matter what you type.

## Explain a Command

Don't know what a command does? Ask Drift:

```bash
drift explain tar -czf archive.tar.gz src/
```

Output:

```
tar -czf archive.tar.gz src/
├── tar    → tape archive utility
├── -c     → create a new archive
├── -z     → compress with gzip
├── -f     → specify filename
├── archive.tar.gz → output file
└── src/   → directory to archive
```

## Check Your Setup

```bash
drift doctor
```

## View History

```bash
drift history
```

Shows all your past drift commands with timestamps and outcomes.

## Undo a Mistake

If a command modified files and you want to roll back:

```bash
drift undo
```

This restores files from the last snapshot.

## Slash Commands (ZSH only)

If you have ZSH integration set up, type these directly in your terminal:

```bash
/git      # Analyze repo status, suggest next action
/commit   # Generate a commit message from staged changes
/find     # Smart file search
/test     # Auto-detect and run project tests
```

## What's Next

- [All Commands →](../guide/commands.md) — Complete command reference
- [Safe Execution →](../guide/safe-execution.md) — Test without risk
- [Configuration →](configuration.md) — Customize model, URL, and behavior
