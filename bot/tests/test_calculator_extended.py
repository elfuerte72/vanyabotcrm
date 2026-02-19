"""Extended KBJU calculator tests — precise calculations, edge cases, all activity levels.

All expected values are manually calculated using Mifflin-St Jeor formula.
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_TOKEN", "test_token_fake")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("OPENROUTER_API_KEY", "test_key_fake")

import pytest

from src.services.calculator import calculate_macros, ACTIVITY_MULTIPLIERS, MacroResult


# ─── Helper ──────────────────────────────────────────────────────────────


def _calc_expected(sex: str, weight: float, height: float, age: int,
                   activity: str, goal: str) -> MacroResult:
    """Calculate expected result manually."""
    is_male = sex in ("male", "m", "м")
    if is_male:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    mult = ACTIVITY_MULTIPLIERS.get(activity, 1.375)
    tdee = bmr * mult

    if goal == "weight_loss":
        cals = tdee * 0.85
    elif goal == "muscle_gain":
        cals = tdee * 1.10
    else:
        cals = tdee

    fat_g = weight * 1.0
    protein_coeff = 1.5 if goal in ("weight_loss", "muscle_gain") else 1.4
    protein_coeff = max(1.3, min(1.5, protein_coeff))
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
    def test_male_80kg_180cm_30y_sedentary_weight_loss(self):
        """Male, 80kg, 180cm, 30yo, sedentary, weight loss."""
        result = calculate_macros("male", 80.0, 180.0, 30, "sedentary", "weight_loss")
        expected = _calc_expected("male", 80.0, 180.0, 30, "sedentary", "weight_loss")
        assert result == expected
        # Manual: BMR = 800 + 1125 - 150 + 5 = 1780
        # TDEE = 1780 * 1.2 = 2136
        # Target = 2136 * 0.85 = 1815.6 → 1816
        assert result.calories == 1816

    def test_female_60kg_165cm_25y_moderate_maintenance(self):
        """Female, 60kg, 165cm, 25yo, moderate, maintenance."""
        result = calculate_macros("female", 60.0, 165.0, 25, "moderate", "maintenance")
        expected = _calc_expected("female", 60.0, 165.0, 25, "moderate", "maintenance")
        assert result == expected
        # BMR = 600 + 1031.25 - 125 - 161 = 1345.25
        # TDEE = 1345.25 * 1.55 = 2085.1375 → 2085
        assert result.calories == 2085

    def test_male_100kg_190cm_40y_high_muscle_gain(self):
        """Male, 100kg, 190cm, 40yo, high, muscle gain."""
        result = calculate_macros("male", 100.0, 190.0, 40, "high", "muscle_gain")
        expected = _calc_expected("male", 100.0, 190.0, 40, "high", "muscle_gain")
        assert result == expected
        # BMR = 1000 + 1187.5 - 200 + 5 = 1992.5
        # TDEE = 1992.5 * 1.725 = 3437.0625
        # Target = 3437.0625 * 1.10 = 3780.77 → 3781
        assert result.calories == 3781

    def test_female_50kg_155cm_20y_extreme_weight_loss(self):
        """Female, 50kg, 155cm, 20yo, extreme, weight loss."""
        result = calculate_macros("female", 50.0, 155.0, 20, "extreme", "weight_loss")
        expected = _calc_expected("female", 50.0, 155.0, 20, "extreme", "weight_loss")
        assert result == expected
        # BMR = 500 + 968.75 - 100 - 161 = 1207.75
        # TDEE = 1207.75 * 1.9 = 2294.725
        # Target = 2294.725 * 0.85 = 1950.52 → 1951
        assert result.calories == 1951


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
        # Should be lower due to age penalty
        result_young = calculate_macros("female", 55.0, 160.0, 25, "sedentary", "maintenance")
        assert result.calories < result_young.calories

    def test_carbs_never_negative_extreme_case(self):
        """Very low weight + high activity should not produce negative carbs."""
        result = calculate_macros("female", 40.0, 140.0, 60, "sedentary", "weight_loss")
        assert result.carbs >= 0

    def test_very_heavy_person(self):
        """Very heavy person — protein and fats are proportional to weight."""
        result = calculate_macros("male", 200.0, 190.0, 30, "moderate", "maintenance")
        assert result.fats == 200  # 1 g/kg
        assert result.protein == 280  # 1.4 g/kg for maintenance


# ─── Activity levels: each higher level gives more calories ──────────────


class TestActivityLevels:
    def test_activity_levels_ascending_calories(self):
        """Each activity level produces more calories than the previous."""
        levels = ["sedentary", "light", "moderate", "high", "extreme"]
        results = [
            calculate_macros("male", 80.0, 180.0, 30, level, "maintenance")
            for level in levels
        ]

        for i in range(len(results) - 1):
            assert results[i].calories < results[i + 1].calories, (
                f"{levels[i]} ({results[i].calories}) should be < "
                f"{levels[i + 1]} ({results[i + 1].calories})"
            )

    def test_unknown_activity_defaults_to_light(self):
        """Unknown activity_level defaults to 1.375 (light)."""
        result_unknown = calculate_macros("male", 80.0, 180.0, 30, "ultra_extreme", "maintenance")
        result_light = calculate_macros("male", 80.0, 180.0, 30, "light", "maintenance")
        assert result_unknown.calories == result_light.calories

    def test_all_five_activity_levels_exist(self):
        assert len(ACTIVITY_MULTIPLIERS) == 5
        expected = {"sedentary", "light", "moderate", "high", "extreme"}
        assert set(ACTIVITY_MULTIPLIERS.keys()) == expected


# ─── Macro distribution rules ───────────────────────────────────────────


class TestMacroDistribution:
    def test_fats_always_1g_per_kg(self):
        """Fats are always 1 g/kg of body weight."""
        for weight in [50, 70, 90, 120]:
            result = calculate_macros("male", weight, 180.0, 30, "moderate", "maintenance")
            assert result.fats == weight

    def test_protein_15_for_weight_loss(self):
        """Protein = 1.5 g/kg for weight_loss."""
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "weight_loss")
        assert result.protein == 120  # 80 * 1.5

    def test_protein_15_for_muscle_gain(self):
        """Protein = 1.5 g/kg for muscle_gain."""
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "muscle_gain")
        assert result.protein == 120

    def test_protein_14_for_maintenance(self):
        """Protein = 1.4 g/kg for maintenance."""
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert result.protein == 112  # 80 * 1.4

    def test_carbs_are_remaining_calories(self):
        """Carbs = (calories - protein*4 - fats*9) / 4."""
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        expected_carb_cals = result.calories - result.protein * 4 - result.fats * 9
        expected_carbs = round(expected_carb_cals / 4)
        assert abs(result.carbs - expected_carbs) <= 1  # rounding tolerance


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
        # 'f' is not in ("male", "m", "м") → uses female formula
        assert r1 == r2

    def test_male_vs_female_formula_difference(self):
        """Male formula gives higher BMR (+166 difference)."""
        r_male = calculate_macros("male", 70.0, 170.0, 30, "moderate", "maintenance")
        r_female = calculate_macros("female", 70.0, 170.0, 30, "moderate", "maintenance")
        # Male: +5, Female: -161 → difference = 166 * 1.55 = 257.3 calories
        assert r_male.calories > r_female.calories
        assert r_male.calories - r_female.calories == round(166 * 1.55)


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

    def test_weight_loss_is_85_percent_tdee(self):
        """Weight loss = 85% of TDEE."""
        r_loss = calculate_macros("male", 80.0, 180.0, 30, "moderate", "weight_loss")
        r_maint = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert r_loss.calories == round(r_maint.calories * 0.85)

    def test_muscle_gain_is_110_percent_tdee(self):
        """Muscle gain = 110% of TDEE."""
        r_gain = calculate_macros("male", 80.0, 180.0, 30, "moderate", "muscle_gain")
        r_maint = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert r_gain.calories == round(r_maint.calories * 1.10)

    def test_unknown_goal_is_maintenance(self):
        """Unknown goal treated as maintenance."""
        r_unknown = calculate_macros("male", 80.0, 180.0, 30, "moderate", "unknown_goal")
        r_maint = calculate_macros("male", 80.0, 180.0, 30, "moderate", "maintenance")
        assert r_unknown.calories == r_maint.calories

    def test_all_results_are_integers(self):
        """All result fields are int."""
        result = calculate_macros("male", 80.0, 180.0, 30, "moderate", "weight_loss")
        assert isinstance(result.calories, int)
        assert isinstance(result.protein, int)
        assert isinstance(result.fats, int)
        assert isinstance(result.carbs, int)
