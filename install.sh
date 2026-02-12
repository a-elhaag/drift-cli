#!/usr/bin/env bash
# Drift CLI Installer for macOS
# Installs Ollama, Drift CLI, and ZSH integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DRIFT_DIR="$HOME/.drift"
DRIFT_MODEL="qwen2.5-coder:1.5b"
OLLAMA_URL="https://ollama.com/install.sh"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════╗"
echo "║                                       ║"
echo "║         Drift CLI Installer           ║"
echo "║   Terminal-Native AI Assistant        ║"
echo "║                                       ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This installer is currently only for macOS"
    print_warning "Linux support coming soon!"
    exit 1
fi

# Check Python version
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    print_warning "Install Python 3.9+ from https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
REQUIRED_VERSION="3.9"

if [[ ! "$PYTHON_VERSION" =~ ^3\.[9-9]+ ]] && [[ ! "$PYTHON_VERSION" =~ ^[4-9]\. ]]; then
    print_error "Python 3.9+ is required, but Python $PYTHON_VERSION is installed"
    exit 1
fi
print_success "Python $PYTHON_VERSION found"

# Step 1: Install Ollama if not present
print_status "Checking for Ollama..."
if command -v ollama &> /dev/null; then
    print_success "Ollama is already installed"
else
    print_status "Installing Ollama..."
    curl -fsSL "$OLLAMA_URL" | sh
    print_success "Ollama installed"
fi

# Step 2: Start Ollama if not running
print_status "Checking if Ollama is running..."
if ! pgrep -x "ollama" > /dev/null; then
    print_status "Starting Ollama..."
    # Start Ollama in the background
    nohup ollama serve > /dev/null 2>&1 &
    sleep 3
    print_success "Ollama started"
else
    print_success "Ollama is already running"
fi

# Step 3: Pull the default model
print_status "Pulling Ollama model: $DRIFT_MODEL..."
print_warning "This may take a few minutes..."
if ollama pull "$DRIFT_MODEL"; then
    print_success "Model $DRIFT_MODEL ready"
else
    print_error "Failed to pull model"
    print_warning "You can try manually: ollama pull $DRIFT_MODEL"
fi

# Step 4: Install Python dependencies and Drift CLI
print_status "Installing Drift CLI..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    print_warning "Install Python 3.9+ from https://www.python.org/"
    exit 1
fi

# Check for pipx
if ! command -v pipx &> /dev/null; then
    print_status "Installing pipx..."
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Install Drift CLI using pipx
if [[ -f "$SCRIPT_DIR/pyproject.toml" ]]; then
    # Installing from source
    print_status "Installing from source..."
    pipx install -e "$SCRIPT_DIR" --force
else
    # Installing from PyPI (future)
    print_status "Installing from PyPI..."
    pipx install drift-cli --force
fi

print_success "Drift CLI installed"

# Step 5: Create Drift directory
print_status "Creating Drift directory..."
mkdir -p "$DRIFT_DIR"
mkdir -p "$DRIFT_DIR/snapshots"
print_success "Drift directory created: $DRIFT_DIR"

# Step 6: Install ZSH integration
print_status "Installing ZSH integration..."

# Copy drift.zsh to ~/.drift/
if [[ -f "$SCRIPT_DIR/drift.zsh" ]]; then
    cp "$SCRIPT_DIR/drift.zsh" "$DRIFT_DIR/drift.zsh"
    print_success "drift.zsh copied to $DRIFT_DIR/"
else
    print_error "drift.zsh not found in installer directory"
    exit 1
fi

# Add source line to .zshrc if not already present
ZSHRC="$HOME/.zshrc"
SOURCE_LINE="source ~/.drift/drift.zsh"

if [[ ! -f "$ZSHRC" ]]; then
    print_warning "~/.zshrc not found, creating it..."
    touch "$ZSHRC"
fi

if ! grep -q "drift.zsh" "$ZSHRC"; then
    print_status "Adding Drift to ~/.zshrc..."
    echo "" >> "$ZSHRC"
    echo "# Drift CLI integration" >> "$ZSHRC"
    echo "$SOURCE_LINE" >> "$ZSHRC"
    print_success "Added to ~/.zshrc"
else
    print_success "Already present in ~/.zshrc"
fi

# Step 7: Set default model in environment
ENV_LINE="export DRIFT_MODEL=\"$DRIFT_MODEL\""
if ! grep -q "DRIFT_MODEL" "$ZSHRC"; then
    echo "$ENV_LINE" >> "$ZSHRC"
fi

# Final success message
echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════╗"
echo "║                                       ║"
echo "║    ✓ Installation Complete!           ║"
echo "║                                       ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "🚀 Next steps:"
echo ""
echo "1. Restart your terminal (or run: source ~/.zshrc)"
echo "2. Type a natural language command, e.g.:"
echo "   ${BLUE}find all python files modified today${NC}"
echo "3. Press ${GREEN}Ctrl+Space${NC}"
echo ""
echo "📚 Try these commands:"
echo "  ${BLUE}drift suggest \"your query\"${NC}  - Get command suggestions"
echo "  ${BLUE}drift find \"something\"${NC}      - Smart search"
echo "  ${BLUE}drift explain \"command\"${NC}     - Explain a command"
echo "  ${BLUE}drift history${NC}                - View history"
echo "  ${BLUE}drift doctor${NC}                 - Check system status"
echo ""
echo "💡 Press Ctrl+Space in your terminal to activate Drift anytime!"
echo ""

# Offer to reload shell
read -p "Would you like to reload your shell now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    exec zsh -l
fi
