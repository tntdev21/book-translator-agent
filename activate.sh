#!/bin/bash
# Quick activation script
# Usage: source activate.sh

if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
    echo "Python: $(which python)"

    # WeasyPrint (PDF export) needs pango/gobject. Homebrew's copies live in
    # /opt/homebrew/lib (Apple Silicon) or /usr/local/lib (Intel), neither of
    # which is on the default dyld search path — without this, importing
    # weasyprint fails with "cannot load library 'libgobject-2.0-0'".
    for libdir in /opt/homebrew/lib /usr/local/lib; do
        if [ -d "$libdir" ]; then
            case ":$DYLD_FALLBACK_LIBRARY_PATH:" in
                *":$libdir:"*) ;;
                *) export DYLD_FALLBACK_LIBRARY_PATH="$libdir:$DYLD_FALLBACK_LIBRARY_PATH" ;;
            esac
        fi
    done
else
    echo "❌ Virtual environment not found. Run ./setup.sh first"
fi
