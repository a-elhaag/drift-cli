---
title: "Drift CLI — A Safety-First AI Terminal Assistant Built Entirely with GitHub Copilot"
published: false
description: "I built a terminal AI assistant that converts natural language to shell commands, with safety layers, undo support, and memory — powered by local LLMs and built with GitHub Copilot CLI."
tags: devchallenge, github, copilot, cli
cover_image: ""
---

_This is a submission for the [GitHub Copilot CLI Challenge](https://dev.to/challenges/github-2026-01-21)_

## What I Built

**Drift CLI** is a terminal-native, safety-first AI assistant that turns plain English into shell commands — and makes sure they won't destroy your system before running them.

You type something like `drift suggest "find all Python files modified in the last 24 hours"` and Drift:

1. Queries a **local LLM** (via Ollama — no cloud, no API keys)
2. Generates a structured execution plan with risk assessment
3. Shows you a **dry-run preview** with color-coded risk badges
4. Asks for confirmation before executing anything
5. Takes a **file snapshot** so you can `drift undo` if needed

### Why It Matters To Me

I wanted a tool that makes the terminal feel intelligent _without_ sacrificing safety or privacy. Every AI terminal tool I tried either required cloud API keys, couldn't undo mistakes, or would happily run `rm -rf /` if the LLM hallucinated. Drift is designed to be the opposite:

- **Safety-first**: 60+ blocklist patterns, 3-tier risk scoring, mandatory confirmation for dangerous ops
- **Local-first**: Runs on Ollama, your data never leaves your machine
- **Recoverable**: Snapshot-based undo for every file-modifying operation

### Key Features

| Feature                     | Description                                                   |
| --------------------------- | ------------------------------------------------------------- |
| 🧠 Natural Language → Shell | `drift suggest "compress all logs older than 7 days"`         |
| 🛡️ Safety Engine            | Blocklist, risk scoring (LOW/MEDIUM/HIGH), dry-run defaults   |
| ⏪ Undo System              | File snapshots before every modification                      |
| 📝 Memory                   | Learns your tool preferences and adapts over time             |
| ⚡ Slash Commands           | `/git`, `/commit`, `/find`, `/test` — context-aware shortcuts |
| 🔍 Explain                  | `drift explain "tar -czf archive.tar.gz src/"`                |
| 🩺 Doctor                   | `drift doctor` diagnoses your setup                           |
| 🐳 Isolated Execution       | Mock, sandbox, and Docker executor modes                      |

### Tech Stack

- **Python 3.9+** with Typer (CLI), Pydantic (validation), Rich (UI), httpx (HTTP)
- **Ollama** for local LLM inference (qwen2.5-coder:1.5b by default)
- **ZSH integration** with Ctrl+Space keybinding

## Demo

### GitHub Repository

{% github a-elhaag/drift-cli %}

### Screenshots & Walkthrough

**1. Suggesting commands from natural language:**

```bash
$ drift suggest "find all python files modified today"
```

The output shows a structured plan with risk assessment, command preview, and confirmation prompt — all rendered with Rich panels and color-coded risk badges.

**2. Safety in action — dangerous commands are blocked:**

```bash
$ drift suggest "delete everything"
# ❌ BLOCKED: rm -rf / — Dangerous pattern detected
# Commands with HIGH risk require typing "YES" to confirm
```

**3. Testing safely without touching your system:**

```bash
# Dry-run mode — see what would happen, execute nothing
$ drift suggest "reorganize my project" --dry-run

# Mock executor — commands are logged but never run
$ DRIFT_EXECUTOR=mock drift suggest "clean up temp files"

# Sandbox — real execution but confined to a temp directory
$ DRIFT_SANDBOX_ROOT=/tmp/sandbox drift suggest "create project structure"
```

**4. The memory system learns your preferences:**

```bash
$ drift memory show
# Shows your favorite tools, risk tolerance, common workflows
# Drift adapts its suggestions based on your patterns
```

**5. Slash commands for quick actions:**

```bash
$ /git     # → Analyzes repo status, suggests next action
$ /commit  # → Generates conventional commit message from staged changes
$ /find    # → Smart file search with context awareness
$ /test    # → Auto-detects project type, runs appropriate test command
```

<!--
TODO: Replace with actual video recording.
Record a 2-3 minute terminal session showing:
1. drift suggest "find large files"
2. drift explain "du -sh * | sort -rh | head -10"
3. drift suggest "delete all .pyc files" --dry-run
4. drift memory show
5. /git slash command

Use asciinema or a screen recorder:
  asciinema rec demo.cast
  # ... do the demo ...
  # Upload to asciinema.org and embed here
-->

## My Experience with GitHub Copilot CLI

GitHub Copilot was my primary development partner throughout this entire project. Here's how it shaped the build:

### Architecture & Scaffolding

I started with a rough idea — "terminal AI assistant with safety" — and Copilot helped me design the entire module structure. When I described the safety-first philosophy, it suggested the layered architecture:

- Blocklist → Risk scoring → Dry-run preview → Confirmation → Snapshot → Execute → Undo

This became the backbone of the project. Copilot generated the initial `SafetyChecker` class with regex blocklist patterns, and I iteratively hardened it by asking things like _"what other destructive shell patterns should be blocked?"_ and _"add Docker injection prevention."_

### Code Generation & Iteration

The bulk of the code was generated through conversational iteration with Copilot:

- **Pydantic models** — I described the Plan/Command/RiskLevel schema and Copilot produced the exact models with proper validation
- **Ollama client** — Copilot scaffolded the httpx-based client with retry logic, JSON parsing, and structured prompts
- **Rich UI** — I said "show risk as colored badges in panels" and got the full `DriftUI` class with themed panels, tables, and confirmation flows
- **Executor pattern** — Copilot suggested the Mock/Local/Docker executor abstraction which became the foundation for safe testing

### Bug Fixes & Security

Copilot was instrumental in finding and fixing security issues:

1. **Shell injection** — Identified that `subprocess.run(shell=True)` was dangerous for LLM-generated commands; suggested using `shlex.split()` with `shell=False` when possible
2. **Path traversal** — Found that snapshot restore could write files outside the home directory; added path validation
3. **Docker injection** — Flagged that Docker volume mounts could be exploited; added container command blocklist
4. **Prompt injection** — Suggested input sanitization before sending queries to the LLM

### Refactoring & Cleanup

In the final phase, I used Copilot to audit the entire project for production-readiness. It:

- Identified 29 redundant markdown files from the development process and cleaned them up
- Found a deprecated `safety_old.py` that was superseded but never removed
- Wired the `ConfigManager` (which existed but wasn't connected) into the CLI
- Fixed a failing test where the safety blocklist was correctly blocking a pattern the test expected to pass
- Consolidated 3 redundant quickstart guides into one comprehensive README

### Impact

Without Copilot, this project would have taken significantly longer. The safety patterns alone — 60+ regex rules covering fork bombs, disk operations, crypto miners, base64 exploits — would have required extensive research. Copilot provided them as a starting point and I validated and refined them.

The conversational workflow of _describe intent → get code → test → refine_ made it feel less like coding and more like pair programming with a knowledgeable partner.

---

**Try it yourself:**

```bash
git clone https://github.com/a-elhaag/drift-cli.git
cd drift-cli
pip install -e .
drift doctor
drift suggest "show me the largest files in this directory"
```
