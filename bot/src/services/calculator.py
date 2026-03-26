"""Harris-Benedict KBJU calculator."""

from __future__ import annotations

from dataclasses import dataclass

import structlog

logger = structlog.get_logger()

# Protein coefficients per goal (g per kg of body weight)
PROTEIN_COEFFICIENTS = {
    "weight_loss": 1.7,
    "muscle_gain": 1.5,
    "maintenance": 1.2,
}


@dataclass
class MacroResult:
    calories: int
    protein: int
    fats: int
    carbs: int


def calculate_macros(
    sex: str,
    weight: float,
    height: float,
    age: int,
    activity_level: str,
    goal: str,
) -> MacroResult:
    """Calculate KBJU using Harris-Benedict formula.

    BMR × 1.2, then goal adjustment:
      - maintenance: no adjustment
      - muscle_gain (weight_gain): +15%
      - weight_loss: −20%

    Protein: 1.2–1.7 g/kg (goal-dependent)
    Fats: 1 g/kg
    Carbs: remaining calories

    Args:
        sex: 'male' or 'female'
        weight: body weight in kg
        height: height in cm
        age: age in years
        activity_level: kept for API compatibility (not used in calculation)
        goal: one of weight_loss/maintenance/muscle_gain/weight_gain

    Returns:
        MacroResult with calories, protein, fats, carbs
    """
    is_male = sex in ("male", "m", "м")

    # BMR (Harris-Benedict)
    if is_male:
        bmr = 88.362 + 13.397 * weight + 4.799 * height - 5.677 * age
    else:
        bmr = 447.593 + 9.247 * weight + 3.098 * height - 4.330 * age

    # Base expenditure: BMR × 1.2
    base = bmr * 1.2

    # Goal adjustment
    if goal == "weight_loss":
        target_calories = base * 0.80
    elif goal in ("muscle_gain", "weight_gain"):
        target_calories = base * 1.15
    else:
        target_calories = base

    # Macros
    # Fat: 1 g/kg
    fat_g = weight * 1.0
    fat_cals = fat_g * 9

    # Protein: 1.2–1.7 g/kg depending on goal
    normalized_goal = "muscle_gain" if goal == "weight_gain" else goal
    protein_coeff = PROTEIN_COEFFICIENTS.get(normalized_goal, 1.2)
    protein_g = weight * protein_coeff
    protein_cals = protein_g * 4

    # Carbs: remaining calories
    carb_cals = target_calories - protein_cals - fat_cals
    if carb_cals < 0:
        carb_cals = 0
    carb_g = carb_cals / 4

    result = MacroResult(
        calories=round(target_calories),
        protein=round(protein_g),
        fats=round(fat_g),
        carbs=round(carb_g),
    )

    logger.debug(
        "macros_calculated",
        sex=sex, weight=weight, height=height, age=age,
        activity=activity_level, goal=goal,
        result=result,
    )

    return result
