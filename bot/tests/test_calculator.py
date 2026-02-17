"""Tests for Mifflin-St Jeor KBJU calculator."""

from src.services.calculator import calculate_macros, ACTIVITY_MULTIPLIERS


class TestCalculateMacros:
    def test_male_moderate_weight_loss(self):
        result = calculate_macros(
            sex="male", weight=80, height=180, age=30,
            activity_level="moderate", goal="weight_loss",
        )
        # BMR = 10*80 + 6.25*180 - 5*30 + 5 = 800+1125-150+5 = 1780
        # TDEE = 1780 * 1.55 = 2759
        # Target = 2759 * 0.85 = 2345.15 → 2345
        assert result.calories == 2345
        assert result.protein == 120  # 80 * 1.5
        assert result.fats == 80  # 80 * 1.0
        assert result.carbs > 0

    def test_female_sedentary_maintenance(self):
        result = calculate_macros(
            sex="female", weight=60, height=165, age=25,
            activity_level="sedentary", goal="maintenance",
        )
        # BMR = 10*60 + 6.25*165 - 5*25 - 161 = 600+1031.25-125-161 = 1345.25
        # TDEE = 1345.25 * 1.2 = 1614.3 → 1614
        assert result.calories == 1614
        assert result.protein == 84  # 60 * 1.4
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
        # ~10% above TDEE (rounding may differ by 1)
        assert abs(gain.calories - round(maintenance.calories * 1.10)) <= 1

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

    def test_unknown_activity_defaults_to_light(self):
        result = calculate_macros(
            sex="male", weight=70, height=170, age=25,
            activity_level="unknown_level", goal="maintenance",
        )
        light = calculate_macros(
            sex="male", weight=70, height=170, age=25,
            activity_level="light", goal="maintenance",
        )
        assert result.calories == light.calories

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

    def test_all_activity_levels_exist(self):
        expected = {"sedentary", "light", "moderate", "high", "extreme"}
        assert set(ACTIVITY_MULTIPLIERS.keys()) == expected

    def test_carbs_never_negative(self):
        # Very low calorie scenario
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
