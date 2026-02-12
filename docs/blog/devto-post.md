# DEV.to Challenge Submission

> _This is the full text of our submission to the [GitHub Copilot CLI Challenge](https://dev.to/challenges/github-2026-01-21) on DEV.to._

---

## Drift CLI — A Safety-First AI Terminal Assistant Built Entirely with GitHub Copilot

_This is a submission for the [GitHub Copilot CLI Challenge](https://dev.to/challenges/github-2026-01-21)_

### What I Built

**Drift CLI** is a terminal-native, safety-first AI assistant that turns plain English into shell commands — and makes sure they won't destroy your system before running them.

You type something like `drift suggest "find all Python files modified in the last 24 hours"` and Drift:

1. Queries a **local LLM** (via Ollama — no cloud, no API keys)
2. Generates a structured execution plan with risk assessment
3. Shows you a **dry-run preview** with color-coded risk badges
4. Asks for confirmation before executing anything
5. Takes a **file snapshot** so you can `drift undo` if needed

#### Why It Matters

I wanted a tool that makes the terminal feel intelligent _without_ sacrificing safety or privacy. Every AI terminal tool I tried either required cloud API keys, couldn't undo mistakes, or would happily run `rm -rf /` if the LLM hallucinated. Drift is designed to be the opposite:

- **Safety-first**: 60+ blocklist patterns, 3-tier risk scoring, mandatory confirmation for dangerous ops
- **Local-first**: Runs on Ollama, your data never leaves your machine
- **Recoverable**: Snapshot-based undo for every file-modifying operation

#### Key Features

| Feature                          | Description                                                   |
| -------------------------------- | ------------------------------------------------------------- |
| :brain: Natural Language → Shell | `drift suggest "compress all logs older than 7 days"`         |
| :shield: Safety Engine           | Blocklist, risk scoring (LOW/MEDIUM/HIGH), dry-run defaults   |
| :rewind: Undo System             | File snapshots before every modification                      |
| :memo: Memory                    | Learns your tool preferences and adapts over time             |
| :zap: Slash Commands             | `/git`, `/commit`, `/find`, `/test` — context-aware shortcuts |
| :mag: Explain                    | `drift explain "tar -czf archive.tar.gz src/"`                |
| :stethoscope: Doctor             | `drift doctor` diagnoses your setup                           |
| :whale: Isolated Execution       | Mock, sandbox, and Docker executor modes                      |

#### Tech Stack

- **Python 3.9+** with Typer (CLI), Pydantic (validation), Rich (UI), httpx (HTTP)
- **Ollama** for local LLM inference (qwen2.5-coder:1.5b by default)
- **ZSH integration** with Ctrl+Space keybinding

### Demo

#### GitHub Repository

[github.com/a-elhaag/drift-cli](https://github.com/a-elhaag/drift-cli)

#### Walkthrough

**1. Suggesting commands from natural language:**

```bash
$ drift suggest "find all python files modified today"
╭─ Plan ──────────────────────────────────────────────────────╮
│  Summary: Find recently modified Python files               │
│  Risk: 🟢 LOW                                              │
│  $ find . -type f -name '*.py' -mtime -1                   │
╰──────────────────────────────────────────────────────────────╯
Execute? [y/N]:
```

**2. Safety in action — dangerous commands are blocked:**

```bash
$ drift suggest "delete everything"
# ❌ BLOCKED: rm -rf / — Dangerous pattern detected
```

**3. Safe testing modes:**

```bash
# Dry-run — see the plan, never execute
drift suggest "reorganize my project" --dry-run

# Mock executor — commands logged but never run
DRIFT_EXECUTOR=mock drift suggest "clean up temp files"

# Sandbox — real execution confined to a temp directory
DRIFT_SANDBOX_ROOT=/tmp/sandbox drift suggest "create project structure"
```

**4. The memory system learns your preferences:**

```bash
$ drift memory show
# Shows: preferred tools, risk tolerance, common workflows
```

### My Experience with GitHub Copilot CLI

GitHub Copilot was my primary development partner throughout this entire project.

#### Architecture & Scaffolding

I started with a rough idea — "terminal AI assistant with safety" — and Copilot helped design the layered architecture:

```
Blocklist → Risk Scoring → Dry-Run → Confirmation → Snapshot → Execute → Undo
```

This became the backbone of the project. Copilot generated the initial `SafetyChecker` class with regex blocklist patterns, and I iteratively hardened it by asking things like _"what other destructive shell patterns should be blocked?"_ and _"add Docker injection prevention."_

#### Code Generation & Iteration

- **Pydantic models** — I described the Plan/Command/RiskLevel schema and Copilot produced the exact models with proper validation
- **Ollama client** — Copilot scaffolded the httpx-based client with retry logic, JSON parsing, and structured prompts
- **Rich UI** — I said "show risk as colored badges in panels" and got the full `DriftUI` class with themed panels, tables, and confirmation flows
- **Executor pattern** — Copilot suggested the Mock/Local/Docker executor abstraction which became the foundation for safe testing

#### Bug Fixes & Security

1. **Shell injection** — Identified `subprocess.run(shell=True)` as dangerous; suggested `shlex.split()` with `shell=False`
2. **Path traversal** — Found snapshot restore could write outside home directory; added path validation
3. **Docker injection** — Flagged volume mount exploits; added container command blocklist
4. **Prompt injection** — Suggested input sanitization before LLM queries

#### Production Cleanup

In the final phase, Copilot audited the project:

- Identified and removed 29 redundant files from the development process
- Found deprecated code that was never cleaned up
- Wired an existing ConfigManager that wasn't connected to the CLI
- Fixed a failing test caused by improved safety blocklist
- Consolidated 3 quickstart guides into one comprehensive README

#### Impact

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

---

[:material-arrow-left: Back to docs](../index.md)
