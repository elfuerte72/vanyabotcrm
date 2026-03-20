#!/usr/bin/env bash
# Reset test user 379336096 for manual testing.
# Usage: ./reset_test_user.sh

set -euo pipefail

CHAT_ID=379336096

# Load DATABASE_URL from bot/.env
if [ -f "$(dirname "$0")/bot/.env" ]; then
  set -a
  source "$(dirname "$0")/bot/.env"
  set +a
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL not set"
  exit 1
fi

echo "Deleting test user $CHAT_ID..."
psql "$DATABASE_URL" \
  -c "DELETE FROM chat_histories WHERE session_id = '$CHAT_ID';" \
  -c "DELETE FROM user_events WHERE chat_id = $CHAT_ID;" \
  -c "DELETE FROM users_nutrition WHERE chat_id = $CHAT_ID;"
echo "Done."
