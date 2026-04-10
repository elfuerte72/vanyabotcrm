-- Fix user_events.created_at to use timestamptz (consistent with chat_histories)
ALTER TABLE user_events
  ALTER COLUMN created_at TYPE timestamptz
  USING created_at AT TIME ZONE 'UTC';
