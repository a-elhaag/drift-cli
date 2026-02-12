#!/usr/bin/env zsh
# Drift CLI ZSH Integration
# Supports both Ctrl+Space and Enter key for slash commands

# Widget function that gets called on Ctrl+Space
drift-widget() {
    # Save the current buffer (what the user typed)
    local query="$BUFFER"
    
    # If buffer is empty, show help
    if [[ -z "$query" ]]; then
        echo ""
        echo "💡 Drift CLI - Natural Language Terminal Assistant"
        echo ""
        echo "   Ways to use Drift:"
        echo "   1. Type natural language, press Ctrl+Space"
        echo "   2. Type a slash command (e.g., /git), press Enter"
        echo ""
        echo "   Examples:"
        echo "   • find all python files modified today"
        echo "   • /commit (smart commit with AI message)"
        echo "   • /find *.py (quick file search)"
        echo "   • /help (show all slash commands)"
        zle reset-prompt
        return
    fi
    
    # Clear the current buffer and show processing
    echo ""
    echo "🤔 Processing: $query"
    
    # Call drift suggest with dry-run to show preview
    local output=$(drift suggest "$query" --dry-run 2>&1)
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        # Display the output
        echo "$output"
        echo ""
        
        # Try to extract and inject the first command into BUFFER
        # This is a simple extraction - looks for lines starting with common commands
        local extracted_cmd=$(echo "$output" | grep -E '^\s*(find|ls|git|rm|mv|cp|cat|grep|sed|awk|tar|zip|chmod|chown|mkdir|touch|echo|python|node|ruby|npm|pip|brew|apt|docker|kubectl|curl|wget)' | head -1 | sed 's/^\s*//')
        
        if [[ -n "$extracted_cmd" ]]; then
            # Inject the command into BUFFER for user to edit/confirm
            BUFFER="$extracted_cmd"
            zle end-of-line
        else
            # No command extracted, clear buffer to let user type again
            BUFFER=""
        fi
    else
        # Error occurred
        echo "[ERROR] Drift failed:"
        echo "$output"
        BUFFER=""
    fi
    
    zle reset-prompt
}

# Widget for handling Enter key with slash commands
drift-enter-widget() {
    local buffer="$BUFFER"
    
    # Check if buffer starts with / (slash command)
    if [[ "$buffer" =~ ^/[a-z]+ ]]; then
        # This is a slash command - intercept and process with Drift
        echo ""
        echo "🔍 Processing slash command: $buffer"
        
        # Call drift suggest with the slash command
        drift suggest "$buffer"
        
        # Clear buffer after execution
        BUFFER=""
        zle reset-prompt
    else
        # Not a slash command - execute normally
        zle accept-line
    fi
}

# Register the widgets
zle -N drift-widget
zle -N drift-enter-widget

# Bind Ctrl+Space to drift widget
# ^@ is the notation for Ctrl+Space in ZSH
bindkey "^ " drift-widget

# Bind Enter to drift-enter-widget (with fallback to normal behavior)
bindkey "^M" drift-enter-widget

# Alternative: Bind to Ctrl+G if Ctrl+Space doesn't work
# bindkey "^G" drift-widget

# Show a message when sourced (only once)
if [[ -z "$DRIFT_ZSH_LOADED" ]]; then
    echo "✓ Drift CLI loaded"
    echo "  • Press Ctrl+Space for natural language commands"
    echo "  • Type /command and press Enter for quick actions"
    echo "  • Type /help for available slash commands"
    export DRIFT_ZSH_LOADED=1
fi

