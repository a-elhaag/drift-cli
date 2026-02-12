# Drift CLI

<p style="font-size: 1.25em; color: #aaa;">
A terminal-native, safety-first AI assistant that integrates directly into your shell.<br>
Powered by local LLMs via Ollama — no cloud dependency, full privacy.
</p>

---

## :rocket: What is Drift?

Drift turns plain English into safe, executable shell commands. You describe what you want, and Drift:

1. Queries a **local LLM** (via Ollama — no cloud, no API keys)
2. Generates a structured **execution plan** with risk assessment
3. Shows a **dry-run preview** with color-coded risk badges
4. Asks for **confirmation** before executing anything
5. Takes a **file snapshot** so you can `drift undo` if needed

```bash
$ drift suggest "find all Python files modified in the last 7 days"

╭─ Plan ──────────────────────────────────────────────────────╮
│  Summary: Find recently modified Python files               │
│  Risk: 🟢 LOW                                              │
│                                                              │
│  $ find . -type f -name '*.py' -mtime -7                   │
│    → Search for .py files modified within 7 days            │
╰──────────────────────────────────────────────────────────────╯
Execute? [y/N]:
```

## :shield: Safety First

Every command goes through a **three-layer** safety pipeline before it can run:

| Layer            | What It Does                                                                     |
| ---------------- | -------------------------------------------------------------------------------- |
| **Blocklist**    | 60+ regex patterns block dangerous commands (`rm -rf /`, fork bombs, disk wipes) |
| **Risk Scoring** | Commands get a LOW / MEDIUM / HIGH risk badge                                    |
| **Confirmation** | You always review and confirm before execution                                   |

Plus: **snapshot-based undo** for every file-modifying operation.

## :zap: Quick Start

```bash
# Install
git clone https://github.com/a-elhaag/drift-cli.git
cd drift-cli
pip install -e .

# Make sure Ollama is running
ollama pull qwen2.5-coder:1.5b

# Try it
drift suggest "show disk usage by folder"
drift explain "tar -czf archive.tar.gz src/"
drift doctor
```

[Get started :material-arrow-right:](getting-started/installation.md){ .md-button .md-button--primary }
[View on GitHub :material-github:](https://github.com/a-elhaag/drift-cli){ .md-button }

## :sparkles: Key Features

<div class="grid cards" markdown>

- :brain:{ .lg .middle } **Natural Language → Shell**

  ***

  Describe what you want in plain English. Drift generates the right command.

  `drift suggest "compress all logs older than 7 days"`

- :shield:{ .lg .middle } **Safety Engine**

  ***

  Blocklist, risk scoring, dry-run previews, and mandatory confirmation for dangerous ops.

- :floppy_disk:{ .lg .middle } **Undo System**

  ***

  Every file-modifying command creates a snapshot. Roll back anytime with `drift undo`.

- :bulb:{ .lg .middle } **Memory System**

  ***

  Learns your tool preferences and adapts suggestions over time.

- :zap:{ .lg .middle } **Slash Commands**

  ***

  `/git`, `/commit`, `/find`, `/test` — context-aware shortcuts for common workflows.

- :lock:{ .lg .middle } **Local-First & Private**

  ***

  Runs entirely on your machine via Ollama. Your data never leaves your computer.

</div>

## Built with GitHub Copilot

Drift CLI was built entirely with **GitHub Copilot** as a development partner — from architecture design to security hardening. [Read the full story :material-arrow-right:](blog/copilot-experience.md)
