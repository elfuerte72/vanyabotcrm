#!/bin/bash
# Run EN funnel scripts from any directory
# Usage: ./scripts_en/run.sh stage_0.py
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT_DIR="$(dirname "$SCRIPT_DIR")/bot"

if [ -z "$1" ]; then
    echo "Usage: ./scripts_en/run.sh <script_name>"
    echo "Examples:"
    echo "  ./scripts_en/run.sh stage_0.py"
    echo "  ./scripts_en/run.sh reset.py"
    echo ""
    echo "Available scripts:"
    ls "$SCRIPT_DIR"/stage_*.py "$SCRIPT_DIR"/reset.py 2>/dev/null | xargs -n1 basename
    exit 1
fi

cd "$BOT_DIR"
exec uv run python "$SCRIPT_DIR/$1"
