-- Add funnel_variant column for zone-based RU funnel branching
-- Values: 'belly' | 'thighs' | 'arms' | 'glutes' | NULL
ALTER TABLE users_nutrition
ADD COLUMN IF NOT EXISTS funnel_variant TEXT DEFAULT NULL;

-- Update max funnel stage for RU: 7 → 12 (13 stages: 0-12)
-- No constraint needed — stage is managed by application logic
