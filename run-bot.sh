#!/usr/bin/env bash
# Start the Telegram bot
cd "$(dirname "$0")/bot" && exec uv run python -m src.main
