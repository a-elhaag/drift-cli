# Installation

## Prerequisites

| Requirement | Version | Notes                        |
| ----------- | ------- | ---------------------------- |
| **macOS**   | 12+     | Linux support planned        |
| **Python**  | 3.9+    | `python3 --version` to check |
| **Ollama**  | Latest  | Local LLM runtime            |

## Install Ollama

Drift uses [Ollama](https://ollama.com) for local LLM inference. Install it first:

```bash
# macOS — download from ollama.com or:
brew install ollama

# Start Ollama
open -a Ollama    # or: ollama serve
```

Pull the default model:

```bash
ollama pull qwen2.5-coder:1.5b
```

!!! tip "Model choice"
`qwen2.5-coder:1.5b` (~1GB) is fast and works well for command generation. For better quality, try `qwen2.5-coder:7b` (~4.5GB) or `codellama:7b`.

## Install Drift CLI

=== "From Source (recommended)"

    ```bash
    git clone https://github.com/a-elhaag/drift-cli.git
    cd drift-cli
    pip install -e .
    ```

=== "With install script"

    ```bash
    git clone https://github.com/a-elhaag/drift-cli.git
    cd drift-cli
    ./install.sh
    ```

## Verify Installation

```bash
# Check everything is set up correctly
drift doctor
```

Expected output:

```
✓ Ollama is running
✓ Drift directory exists (~/.drift)
✓ Model available: qwen2.5-coder:1.5b
```

## ZSH Integration (Optional)

The installer sets up a `Ctrl+Space` hotkey so you can type natural language directly in your terminal:

```bash
# If not set up automatically, add to ~/.zshrc:
source ~/.drift/drift.zsh
```

Then restart your terminal. Type a natural language query and press `Ctrl+Space`.

## Next Steps

- [Quick Start →](quickstart.md) — Try your first commands
- [Configuration →](configuration.md) — Customize Drift settings
