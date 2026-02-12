# How GitHub Copilot Helped Me Build Drift CLI

> _This page documents how GitHub Copilot was used as a development partner throughout the entire Drift CLI project — from architecture design to security hardening, testing, and production cleanup._

---

## The Starting Point

I had a rough idea: **a terminal AI assistant that's actually safe to use**. Every AI CLI tool I tried either required cloud API keys, couldn't undo mistakes, or would happily run `rm -rf /` if the LLM hallucinated.

I wanted something local-first, safety-first, and recoverable. GitHub Copilot helped me turn that concept into working software.

## Architecture & Scaffolding

When I described the safety-first philosophy, Copilot helped design the layered architecture that became the backbone of the project:

```
Blocklist → Risk Scoring → Dry-Run Preview → Confirmation → Snapshot → Execute → Undo
```

This pipeline ensures that **no command runs without passing through multiple safety gates**. Copilot generated the initial `SafetyChecker` class with regex blocklist patterns, and I iteratively hardened it by asking questions like:

- _"What other destructive shell patterns should be blocked?"_
- _"Add Docker injection prevention"_
- _"What about base64-obfuscated commands?"_

Each time, Copilot produced targeted regex patterns that I validated and added to the blocklist. The final count: **60+ patterns** covering fork bombs, disk wipes, crypto miners, reverse shells, and more.

## Code Generation Through Conversation

The bulk of the code was generated through conversational iteration:

### Pydantic Models

I described the Plan/Command/RiskLevel schema in plain English, and Copilot produced the exact Pydantic models with proper validation, enums, and field descriptions.

### Ollama Client

Copilot scaffolded the httpx-based client with:

- Retry logic with exponential backoff
- JSON mode forcing for structured output
- System prompt engineering for consistent responses
- Input sanitization to prevent prompt injection

### Rich Terminal UI

I said _"show risk as colored badges in panels"_ and got the full `DriftUI` class with themed panels, tables, and multi-level confirmation flows.

### Executor Pattern

When I asked for safe testing options, Copilot suggested the Mock/Local/Docker executor abstraction — an abstract base class with three implementations:

| Executor         | What It Does                           |
| ---------------- | -------------------------------------- |
| `MockExecutor`   | Logs commands, never runs them         |
| `LocalExecutor`  | Runs commands in a sandboxed directory |
| `DockerExecutor` | Runs commands inside a container       |

This became the foundation for safe testing without risking the host system.

## Bug Fixes & Security Hardening

Copilot was instrumental in finding and fixing security issues:

1. **Shell injection** — Identified that `subprocess.run(shell=True)` was dangerous for LLM-generated commands. Suggested using `shlex.split()` with `shell=False` when possible, falling back to `shell=True` only for pipes and redirects.

2. **Path traversal** — Found that snapshot restore could write files outside the home directory. Added path validation to prevent `../../etc/passwd` style attacks.

3. **Docker injection** — Flagged that Docker volume mounts could be exploited. Added container command patterns to the blocklist.

4. **Prompt injection** — Suggested input sanitization before sending user queries to the LLM, stripping control characters and limiting query length.

## Production Audit & Cleanup

In the final phase, I used Copilot to audit the entire project for production-readiness:

- **Identified 29 redundant markdown files** from the development process (old summaries, checklists, reports) and cleaned them up
- **Found deprecated code** (`safety_old.py`) that was superseded but never removed
- **Wired the ConfigManager** which existed in the codebase but wasn't connected to the CLI
- **Fixed a failing test** where an improved safety blocklist was correctly blocking a pattern the test expected to pass
- **Consolidated documentation** from 3 redundant quickstart guides into one comprehensive README

## Test Suite Development

Copilot helped build a comprehensive test suite covering:

- **Safety engine** — Tests for blocked commands, safe commands, risk assessment, and command validation
- **Pydantic models** — Validation of Plan, Command, and RiskLevel schemas
- **Executor integration** — Mock, Local, Sandbox isolation, and execution result tracking
- **23 tests total**, all passing

## Writing This Documentation

Even this documentation site was set up with Copilot's help — MkDocs configuration, Material theme setup, page structure, and the GitHub Actions workflow for automated deployment.

## Impact

Without GitHub Copilot, this project would have taken significantly longer. The safety patterns alone — 60+ regex rules covering fork bombs, disk operations, crypto miners, base64 exploits — would have required extensive security research. Copilot provided them as a starting point and I validated and refined each one.

The conversational workflow of **describe intent → get code → test → refine** made it feel less like coding and more like pair programming with a knowledgeable partner.

---

## Try It Yourself

```bash
git clone https://github.com/a-elhaag/drift-cli.git
cd drift-cli
pip install -e .
drift doctor
drift suggest "show me the largest files in this directory"
```

[:material-github: View on GitHub](https://github.com/a-elhaag/drift-cli){ .md-button .md-button--primary }
[:material-dev-to: Read the DEV.to Post](devto-post.md){ .md-button }
