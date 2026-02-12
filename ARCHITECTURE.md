# Drift CLI Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User Terminal                        │
│  "find all python files modified today" + Ctrl+Space        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   ZSH Integration (drift.zsh)                │
│  - Reads BUFFER                                              │
│  - Calls: drift suggest "$BUFFER"                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLI Layer (cli.py)                        │
│  Commands: suggest, find, explain, history, undo, doctor     │
└───┬──────────────────────┬──────────────────┬───────────────┘
    │                      │                  │
    │                      │                  │
    ▼                      ▼                  ▼
┌──────────┐      ┌──────────────┐     ┌─────────────┐
│  Ollama  │      │   Safety     │     │   History   │
│  Client  │      │   Checker    │     │   Manager   │
└──────────┘      └──────────────┘     └─────────────┘
    │                      │                  │
    │                      │                  │
    ▼                      ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Workflow                           │
│                                                               │
│  1. Get context (cwd, user, git info)                        │
│  2. Query Ollama with structured prompt                      │
│  3. Validate JSON response (Pydantic)                        │
│  4. Check safety (blocklist + risk)                          │
│  5. Display plan (Rich UI)                                   │
│  6. Confirm with user                                        │
│  7. Create snapshot (if modifying files)                     │
│  8. Execute commands                                         │
│  9. Show results                                             │
│  10. Save to history                                         │
└─────────────────────────────────────────────────────────────┘
```

## Module Breakdown

### Core Modules (`drift_cli/core/`)

#### `ollama.py` - Ollama API Client
- Communicates with local Ollama instance
- Forces JSON output format
- Validates responses with Pydantic
- Provides context-aware prompting

Key Methods:
- `get_plan(query, context)` → Returns validated Plan
- `explain_command(command)` → Returns explanation string
- `is_available()` → Health check

#### `safety.py` - Safety Validation
- Hard blocklist of dangerous commands
- Risk level assessment (LOW/MEDIUM/HIGH)
- Command validation pipeline

Key Components:
- `HARD_BLOCKLIST` - Regex patterns for blocked commands
- `HIGH_RISK_PATTERNS` - High-risk indicators
- `MEDIUM_RISK_PATTERNS` - Medium-risk indicators

#### `executor.py` - Command Execution
- Safe command execution with timeout
- Snapshot creation before modifications
- Context gathering (cwd, git, user)
- Sequential command execution with failure handling

#### `history.py` - History & Snapshots
- JSONL-based history storage
- File snapshot management
- Undo/restore functionality
- Snapshot metadata tracking

#### `config.py` - Configuration
- User preferences management
- Model selection
- Ollama URL configuration
- Default settings

### UI Layer (`drift_cli/ui/`)

#### `display.py` - Rich-based Interface
- Plan visualization (panels, tables)
- Risk badges and color coding
- Confirmation prompts
- Execution results display
- History table rendering

### Data Models (`drift_cli/models.py`)

**Pydantic Models:**
- `Plan` - Complete execution plan from LLM
- `Command` - Single shell command
- `RiskLevel` - Enum (LOW/MEDIUM/HIGH)
- `HistoryEntry` - Stored command history
- `ClarificationQuestion` - For ambiguous queries

### CLI Interface (`drift_cli/cli.py`)

**Commands:**
- `suggest <query>` - Main command suggestion
- `find <query>` - Read-only search operations
- `explain <command>` - Command explanation
- `history` - View past operations
- `again` - Re-run last command
- `undo` - Restore from snapshot
- `doctor` - System diagnostics

### Shell Integration (`drift.zsh`)

**ZSH Widget:**
- Bound to Ctrl+Space
- Reads current buffer
- Calls Drift CLI
- Non-blocking execution

## Data Flow

### 1. Query Processing
```
Natural Language
    ↓
Context Gathering (cwd, git, user)
    ↓
System Prompt + User Query
    ↓
Ollama API (JSON mode)
    ↓
Raw JSON Response
    ↓
Pydantic Validation
    ↓
Validated Plan Object
```

### 2. Safety Validation
```
Plan with Commands
    ↓
For each command:
  - Check HARD_BLOCKLIST (regex match)
  - Assess RISK_LEVEL (pattern matching)
  - Collect warnings
    ↓
Safety Report (blocked?, warnings[])
```

### 3. Execution Flow
```
Validated Plan
    ↓
Display Plan (Rich UI)
    ↓
User Confirmation (based on risk level)
    ↓
Create Snapshot (if affected_files exists)
    ↓
Execute Commands (sequential)
    ↓
Collect Output
    ↓
Save to History (JSONL)
    ↓
Display Results
```

## File System Structure

```
~/.drift/
├── config.json           # User configuration
├── history.jsonl         # Command history (append-only)
├── drift.zsh            # ZSH integration script
└── snapshots/
    ├── {uuid-1}/
    │   ├── metadata.json
    │   └── {original files}
    └── {uuid-2}/
        ├── metadata.json
        └── {original files}
```

### History Format (JSONL)
```json
{"timestamp": "2026-02-09T...", "query": "...", "plan": {...}, "executed": true, "exit_code": 0, "snapshot_id": "..."}
```

### Snapshot Metadata
```json
{
  "id": "uuid",
  "timestamp": "2026-02-09T...",
  "files": [
    {"original": "/path/to/file", "snapshot": "/path/in/snapshot"}
  ]
}
```

## LLM Integration

### System Prompt Structure
```
Role: You are Drift, a terminal assistant
Task: Convert natural language to shell commands
Format: Strict JSON schema (Plan model)
Rules:
  - Assess risk accurately
  - Use clarification_needed for ambiguity
  - Provide dry-run versions when possible
  - Never suggest dangerous root operations
Output: JSON matching Plan schema
```

### JSON Schema
```json
{
  "summary": "string",
  "risk": "low|medium|high",
  "commands": [
    {"command": "string", "description": "string", "dry_run": "optional"}
  ],
  "explanation": "string",
  "affected_files": ["optional", "list"],
  "clarification_needed": [
    {"question": "string", "options": ["optional"]}
  ]
}
```

## Safety Architecture

### Three-Layer Defense

1. **LLM Layer**: Trained to avoid dangerous commands
2. **Validation Layer**: Pydantic schema ensures structure
3. **Safety Layer**: Regex-based blocklist + risk assessment

### Risk Assessment Algorithm
```python
if matches(HARD_BLOCKLIST):
    return BLOCKED
elif matches(HIGH_RISK_PATTERNS):
    return HIGH
elif matches(MEDIUM_RISK_PATTERNS):
    return MEDIUM
else:
    return LOW
```

## Extension Points

### Adding a New Command
1. Add function in `cli.py` with `@app.command()` decorator
2. Use existing core modules (ollama, safety, executor)
3. Add tests
4. Update documentation

### Adding Safety Rules
1. Update patterns in `safety.py`
2. Add tests in `test_safety.py`
3. Document in SECURITY.md

### Supporting New Shells
1. Create `drift.{shell}` integration script
2. Add shell detection in `install.sh`
3. Test keybinding compatibility

## Performance Considerations

- **LLM calls**: ~1-3 seconds (local inference)
- **Safety checks**: <10ms (regex matching)
- **Snapshot creation**: O(n) file copies
- **History lookup**: O(n) JSONL scan (optimized with tail)

## Security Boundaries

**Trusted:**
- User confirmation
- Pydantic validation
- Safety blocklist

**Untrusted:**
- LLM output (validated)
- User queries (sanitized in prompts)
- Ollama API responses (validated)

**Attack Surface:**
- LLM hallucinations → Mitigated by validation
- Blocklist bypass → Regex patterns + user confirmation
- Snapshot corruption → Metadata validation
