#!/bin/bash
# Запуск скриптов воронки из любой директории
# Использование: ./scripts/run.sh stage_0.py
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT_DIR="$(dirname "$SCRIPT_DIR")/bot"

if [ -z "$1" ]; then
    echo "Использование: ./scripts/run.sh <script_name>"
    echo "Примеры:"
    echo "  ./scripts/run.sh stage_0.py"
    echo "  ./scripts/run.sh reset.py"
    echo ""
    echo "Доступные скрипты:"
    ls "$SCRIPT_DIR"/stage_*.py "$SCRIPT_DIR"/reset.py 2>/dev/null | xargs -n1 basename
    exit 1
fi

cd "$BOT_DIR"
exec uv run python "$SCRIPT_DIR/$1"
