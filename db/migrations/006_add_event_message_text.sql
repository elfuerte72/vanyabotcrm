-- Add message_text column to store actual funnel/bot message text
ALTER TABLE user_events ADD COLUMN IF NOT EXISTS message_text TEXT;
