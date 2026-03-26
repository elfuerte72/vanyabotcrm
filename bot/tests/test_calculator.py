"""Tests for Harris-Benedict KBJU calculator."""

from src.services.calculator import calculate_macros, PROTEIN_COEFFICIENTS


class TestCalculateMacros:
    def test_male_moderate_weight_loss(self):
        result = calculate_macros(
            sex="male", weight=80, height=180, age=30,
            activity_level="moderate", goal="weight_loss",
        )
        # BMR = 88.362 + 13.397*80 + 4.799*180 - 5.677*30
        #     = 88.362 + 1071.76 + 863.82 - 170.31 = 1853.632
        # Base = 1853.632 * 1.2 = 2224.3584
        # Target = 2224.3584 * 0.80 = 1779.487 → 1779
        assert result.calories == 1779
        assert result.protein == 136  # 80 * 1.7
        assert result.fats == 80  # 80 * 1.0
        assert result.carbs > 0

    def test_female_sedentary_maintenance(self):
        result = calculate_macros(
            sex="female", weight=60, height=165, age=25,
            activity_level="sedentary", goal="maintenance",
        )
        # BMR = 447.593 + 9.247*60 + 3.098*165 - 4.330*25
        #     = 447.593 + 554.82 + 511.17 - 108.25 = 1405.333
        # Base = 1405.333 * 1.2 = 1686.4 → 1686
        assert result.calories == 1686
        assert result.protein == 72  # 60 * 1.2
        assert result.fats == 60  # 60 * 1.0

    def test_muscle_gain_higher_calories(self):
        maintenance = calculate_macros(
            sex="male", weight=75, height=175, age=28,
            activity_level="moderate", goal="maintenance",
        )
        gain = calculate_macros(
            sex="male", weight=75, height=175, age=28,
            activity_level="moderate", goal="muscle_gain",
        )
        assert gain.calories > maintenance.calories
        # +15% above base
        assert abs(gain.calories - round(maintenance.calories * 1.15)) <= 1

    def test_weight_loss_lower_calories(self):
        maintenance = calculate_macros(
            sex="female", weight=65, height=160, age=35,
            activity_level="light", goal="maintenance",
        )
        loss = calculate_macros(
            sex="female", weight=65, height=160, age=35,
            activity_level="light", goal="weight_loss",
        )
        assert loss.calories < maintenance.calories

    def test_activity_level_ignored(self):
        """Activity level param is kept for compatibility but not used."""
        r1 = calculate_macros(
            sex="male", weight=70, height=170, age=25,
            activity_level="sedentary", goal="maintenance",
        )
        r2 = calculate_macros(
            sex="male", weight=70, height=170, age=25,
            activity_level="extreme", goal="maintenance",
        )
        assert r1.calories == r2.calories

    def test_russian_male_sex_indicator(self):
        m_result = calculate_macros(
            sex="м", weight=80, height=180, age=30,
            activity_level="moderate", goal="maintenance",
        )
        male_result = calculate_macros(
            sex="male", weight=80, height=180, age=30,
            activity_level="moderate", goal="maintenance",
        )
        assert m_result.calories == male_result.calories

    def test_protein_coefficients_exist(self):
        expected = {"weight_loss", "muscle_gain", "maintenance"}
        assert set(PROTEIN_COEFFICIENTS.keys()) == expected

    def test_carbs_never_negative(self):
        result = calculate_macros(
            sex="female", weight=100, height=150, age=60,
            activity_level="sedentary", goal="weight_loss",
        )
        assert result.carbs >= 0

    def test_result_types_are_int(self):
        result = calculate_macros(
            sex="male", weight=85.5, height=182.3, age=32,
            activity_level="high", goal="muscle_gain",
        )
        assert isinstance(result.calories, int)
        assert isinstance(result.protein, int)
        assert isinstance(result.fats, int)
        assert isinstance(result.carbs, int)

    def test_weight_gain_alias(self):
        """weight_gain should work same as muscle_gain."""
        r1 = calculate_macros("male", 80, 180, 30, "moderate", "muscle_gain")
        r2 = calculate_macros("male", 80, 180, 30, "moderate", "weight_gain")
        assert r1.calories == r2.calories
        assert r1.protein == r2.protein
