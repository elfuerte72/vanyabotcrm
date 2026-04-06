#!/bin/bash
# Run RU funnel scripts from any directory
# Usage: ./scripts/run.sh belly/stage_0.py
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT_DIR="$(dirname "$SCRIPT_DIR")/bot"

if [ -z "$1" ]; then
    echo "Usage: ./scripts/run.sh <funnel>/<script>"
    echo "Examples:"
    echo "  ./scripts/run.sh belly/stage_0.py"
    echo "  ./scripts/run.sh belly/reset.py"
    echo ""
    echo "Available funnels:"
    for dir in "$SCRIPT_DIR"/*/; do
        [ -f "$dir/_common.py" ] || continue
        name=$(basename "$dir")
        echo "  $name:"
        ls "$dir"/stage_*.py "$dir"/reset.py 2>/dev/null | xargs -n1 basename | sed 's/^/    /'
    done
    exit 1
fi

cd "$BOT_DIR"
exec uv run python "$SCRIPT_DIR/$1"
