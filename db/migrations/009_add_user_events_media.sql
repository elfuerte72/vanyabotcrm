-- Add media column to user_events to store funnel message attachments
-- (photo filenames + video-note flag) so the CRM can render images.
-- Shape: {"photos": ["ru_belly_stage_1.png", ...], "video_note": false}
ALTER TABLE user_events
  ADD COLUMN IF NOT EXISTS media jsonb;
