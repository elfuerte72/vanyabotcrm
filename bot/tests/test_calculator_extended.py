"""Extended KBJU calculator tests — Harris-Benedict formula, precise calculations, edge cases.

All expected values are manually calculated using Harris-Benedict formula.
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

import pytest

from src.services.calculator import calculate_macros, PROTEIN_COEFFICIENTS, MacroResult


# ─── Helper ──────────────────────────────────────────────────────────────


def _calc_expected(sex: str, weight: float, height: float, age: int,
                   activity: str, goal: str) -> MacroResult:
    """Calculate expected result manually using Harris-Benedict."""
    is_male = sex in ("male", "m", "м")
    if is_male:
        bmr = 88.362 + 13.397 * weight + 4.799 * height - 5.677 * age
    else:
        bmr = 447.593 + 9.247 * weight + 3.098 * height - 4.330 * age

    base = bmr * 1.2

    if goal == "weight_loss":
        cals = base * 0.80
    elif goal in ("muscle_gain", "weight_gain"):
        cals = base * 1.15
    else:
        cals = base

    fat_g = weight * 1.0
    normalized_goal = "muscle_gain" if goal == "weight_gain" else goal
    protein_coeff = PROTEIN_COEFFICIENTS.get(normalized_goal, 1.2)
    protein_g = weight * protein_coeff

    carb_cals = cals - protein_g * 4 - fat_g * 9
    if carb_cals < 0:
        carb_cals = 0
    carb_g = carb_cals / 4

    return MacroResult(
        calories=round(cals),
        protein=round(protein_g),
        fats=round(fat_g),
        carbs=round(carb_g),
    )


# ─── Precise calculations for specific profiles ─────────────────────────


class TestPreciseCalculations:
    def test_male_80kg_180cm_30y_weight_loss(self):
        """Male, 80kg, 180cm, 30yo, weight loss."""
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "weight_loss")
        expected = _calc_expected("male", 80.0, 180.0, 30, "moderate", "weight_loss")
        assert result == expected
        # BMR = 88.362 + 1071.76 + 863.82 - 170.31 = 1853.632
        # Base = 1853.632 * 1.2 = 2224.3584
        # Target = 2224.3584 * 0.80 = 1779.487 → 1779
        assert result.calories == 1779

    def test_female_60kg_165cm_25y_maintenance(self):
        """Female, 60kg, 165cm, 25yo, maintenance."""
        result = calculate_macros("female", 60.0, 165.0, 25, "moderate", "maintenance")
        expected = _calc_expected("female", 60.0, 165.0, 25, "moderate", "maintenance")
        assert result == expected
        # BMR = 447.593 + 554.82 + 511.17 - 108.25 = 1405.333
        # Base = 1405.333 * 1.2 = 1686.4 → 1686
        assert result.calories == 1686

    def test_male_100kg_190cm_40y_muscle_gain(self):
        """Male, 100kg, 190cm, 40yo, muscle gain."""
        result = calculate_macros("male", 100.0, 190.0, 40, "high", "muscle_gain")
        expected = _calc_expected("male", 100.0, 190.0, 40, "high", "muscle_gain")
        assert result == expected
        # BMR = 88.362 + 1339.7 + 911.81 - 227.08 = 2112.792
        # Base = 2112.792 * 1.2 = 2535.3504
        # Target = 2535.3504 * 1.15 = 2915.653 → 2916
        assert result.calories == 2916

    def test_female_50kg_155cm_20y_weight_loss(self):
        """Female, 50kg, 155cm, 20yo, weight loss."""
        result = calculate_macros("female", 50.0, 155.0, 20, "extreme", "weight_loss")
        expected = _calc_expected("female", 50.0, 155.0, 20, "extreme", "weight_loss")
        assert result == expected
        # BMR = 447.593 + 462.35 + 480.19 - 86.6 = 1303.533
        # Base = 1303.533 * 1.2 = 1564.2396
        # Target = 1564.2396 * 0.80 = 1251.392 → 1251
        assert result.calories == 1251


# ─── Edge cases: extreme body parameters ────────────────────────────────


class TestEdgeCases:
    def test_minimum_weight_and_height(self):
        """Minimal weight 40kg, height 140cm."""
        result = calculate_macros("female", 40.0, 140.0, 16, "sedentary", "weight_loss")
        assert result.calories > 0
        assert result.protein > 0
        assert result.fats > 0
        assert result.carbs >= 0

    def test_maximum_weight_and_height(self):
        """Large weight 150kg, height 210cm."""
        result = calculate_macros("male", 150.0, 210.0, 40, "extreme", "muscle_gain")
        assert result.calories > 3000
        assert result.protein > 0
        assert result.fats == 150  # 1 g/kg

    def test_young_age_16(self):
        """16 year old."""
        result = calculate_macros("male", 65.0, 175.0, 16, "moderate", "maintenance")
        assert result.calories > 0

    def test_old_age_80(self):
        """80 year old."""
        result = calculate_macros("female", 55.0, 160.0, 80, "sedentary", "maintenance")
        assert result.calories > 0
        result_young = calculate_macros("female", 55.0, 160.0, 25, "sedentary", "maintenance")
        assert result.calories < result_young.calories

    def test_carbs_never_negative_extreme_case(self):
        """Very low weight + high protein should not produce negative carbs."""
        result = calculate_macros("female", 40.0, 140.0, 60, "sedentary", "weight_loss")
        assert result.carbs >= 0

    def test_very_heavy_person(self):
        """Very heavy person — protein and fats are proportional to weight."""
        result = calculate_macros("male", 200.0, 190.0, 30, "moderate", "maintenance")
        assert result.fats == 200  # 1 g/kg
        assert result.protein == 240  # 200 * 1.2 for maintenance


# ─── Activity level is ignored ──────────────────────────────────────────


class TestActivityLevelIgnored:
    def test_all_activity_levels_produce_same_result(self):
        """Activity level is not used — all levels give the same result."""
        levels = ["sedentary", "light", "moderate", "high", "extreme"]
        results = [
            calculate_macros("male", 80.0, 180.0, 30, level, "maintenance")
            for level in levels
        ]
        for r in results[1:]:
            assert r.calories == results[0].calories

    def test_unknown_activity_same_result(self):
        """Unknown activity_level produces same result as any known one."""
        result_unknown = calculate_macros("male", 80.0, 180.0, 30, "ultra_extreme", "maintenance")
        result_moderate = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert result_unknown.calories == result_moderate.calories


# ─── Macro distribution rules ───────────────────────────────────────────


class TestMacroDistribution:
    def test_fats_always_1g_per_kg(self):
        """Fats are always 1 g/kg of body weight."""
        for weight in [50, 70, 90, 120]:
            result = calculate_macros("male", weight, 180.0, 30, "moderate", "maintenance")
            assert result.fats == weight

    def test_protein_17_for_weight_loss(self):
        """Protein = 1.7 g/kg for weight_loss."""
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "weight_loss")
        assert result.protein == 136  # 80 * 1.7

    def test_protein_15_for_muscle_gain(self):
        """Protein = 1.5 g/kg for muscle_gain."""
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "muscle_gain")
        assert result.protein == 120  # 80 * 1.5

    def test_protein_12_for_maintenance(self):
        """Protein = 1.2 g/kg for maintenance."""
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert result.protein == 96  # 80 * 1.2

    def test_carbs_are_remaining_calories(self):
        """Carbs = (calories - protein*4 - fats*9) / 4."""
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        expected_carb_cals = result.calories - result.protein * 4 - result.fats * 9
        expected_carbs = round(expected_carb_cals / 4)
        assert abs(result.carbs - expected_carbs) <= 1


# ─── Sex identifiers ────────────────────────────────────────────────────


class TestSexIdentifiers:
    def test_male_identifiers_same_result(self):
        """'male', 'm', 'м' all produce the same result."""
        r1 = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        r2 = calculate_macros("m", 80.0, 180.0, 30, "moderate", "maintenance")
        r3 = calculate_macros("м", 80.0, 180.0, 30, "moderate", "maintenance")
        assert r1 == r2 == r3

    def test_female_identifiers(self):
        """'female' and other non-male identifiers use female formula."""
        r1 = calculate_macros("female", 60.0, 165.0, 25, "moderate", "maintenance")
        r2 = calculate_macros("f", 60.0, 165.0, 25, "moderate", "maintenance")
        assert r1 == r2

    def test_male_vs_female_formula_difference(self):
        """Male formula gives different BMR than female."""
        r_male = calculate_macros("male", 70.0, 170.0, 30, "moderate", "maintenance")
        r_female = calculate_macros("female", 70.0, 170.0, 30, "moderate", "maintenance")
        assert r_male.calories != r_female.calories


# ─── Goal adjustments ───────────────────────────────────────────────────


class TestGoalAdjustments:
    def test_weight_loss_lower_than_maintenance(self):
        r_loss = calculate_macros("male", 80.0, 180.0, 30, "moderate", "weight_loss")
        r_maint = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert r_loss.calories < r_maint.calories

    def test_muscle_gain_higher_than_maintenance(self):
        r_gain = calculate_macros("male", 80.0, 180.0, 30, "moderate", "muscle_gain")
        r_maint = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert r_gain.calories > r_maint.calories

    def test_weight_loss_is_80_percent_of_base(self):
        """Weight loss = 80% of BMR*1.2."""
        r_loss = calculate_macros("male", 80.0, 180.0, 30, "moderate", "weight_loss")
        r_maint = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert r_loss.calories == round(r_maint.calories * 0.80)

    def test_muscle_gain_is_115_percent_of_base(self):
        """Muscle gain = 115% of BMR*1.2."""
        r_gain = calculate_macros("male", 80.0, 180.0, 30, "moderate", "muscle_gain")
        r_maint = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert r_gain.calories == round(r_maint.calories * 1.15)

    def test_unknown_goal_is_maintenance(self):
        """Unknown goal treated as maintenance."""
        r_unknown = calculate_macros("male", 80.0, 180.0, 30, "moderate", "unknown_goal")
        r_maint = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert r_unknown.calories == r_maint.calories

    def test_all_results_are_integers(self):
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "weight_loss")
        assert isinstance(result.calories, int)
        assert isinstance(result.protein, int)
        assert isinstance(result.fats, int)
        assert isinstance(result.carbs, int)
