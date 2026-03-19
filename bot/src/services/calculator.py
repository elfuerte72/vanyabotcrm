"""Mifflin-St Jeor KBJU calculator."""

from __future__ import annotations

from dataclasses import dataclass

import structlog

logger = structlog.get_logger()

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "high": 1.725,
    "extreme": 1.9,
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
    """Calculate KBJU using Mifflin-St Jeor formula.

    Args:
        sex: 'male' or 'female'
        weight: body weight in kg
        height: height in cm
        age: age in years
        activity_level: one of sedentary/light/moderate/high/extreme
        goal: one of weight_loss/maintenance/muscle_gain

    Returns:
        MacroResult with calories, protein, fats, carbs
    """
    is_male = sex in ("male", "m", "м")

    # BMR (Basal Metabolic Rate)
    if is_male:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # TDEE (Total Daily Energy Expenditure)
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.375)
    tdee = bmr * multiplier

    # Goal adjustment
    if goal == "weight_loss":
        target_calories = tdee * 0.85
    elif goal == "muscle_gain":
        target_calories = tdee * 1.10
    else:
        target_calories = tdee

    # Macros
    # Fat: 1 g/kg (fixed)
    fat_g = weight * 1.0
    fat_cals = fat_g * 9

    # Protein: 1.3-1.5 g/kg depending on goal
    if goal in ("weight_loss", "muscle_gain"):
        protein_coeff = 1.5
    else:
        protein_coeff = 1.4
    protein_coeff = max(1.3, min(1.5, protein_coeff))

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
