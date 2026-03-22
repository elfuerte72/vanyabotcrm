-- Add next_funnel_msg_at column for precise funnel timing
-- RU funnel uses specific MSK times, EN/AR use interval delays
ALTER TABLE users_nutrition ADD COLUMN IF NOT EXISTS next_funnel_msg_at TIMESTAMPTZ;
