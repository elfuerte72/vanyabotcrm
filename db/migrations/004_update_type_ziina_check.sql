-- Update type_ziina CHECK constraint: replace 99 with 129 (upsell stage 10 price)
ALTER TABLE users_nutrition DROP CONSTRAINT IF EXISTS users_nutrition_type_ziina_check;
ALTER TABLE users_nutrition ADD CONSTRAINT users_nutrition_type_ziina_check
  CHECK (type_ziina = ANY (ARRAY[49, 79, 129]));
