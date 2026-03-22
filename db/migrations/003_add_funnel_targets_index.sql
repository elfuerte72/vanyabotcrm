-- Partial index for funnel targets query (scheduler selects users due for next funnel message).
-- Covers: get_food=TRUE, non-buyers, active funnel stage, ordered by next_funnel_msg_at.
CREATE INDEX IF NOT EXISTS idx_funnel_targets
ON users_nutrition (next_funnel_msg_at)
WHERE get_food = TRUE
  AND (is_buyer IS FALSE OR is_buyer IS NULL)
  AND funnel_stage >= 0;
