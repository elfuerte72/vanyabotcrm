-- Add created_at to chat_histories for chronological sorting with user_events
ALTER TABLE chat_histories ADD COLUMN IF NOT EXISTS created_at timestamptz DEFAULT now();
