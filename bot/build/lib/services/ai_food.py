"""AGENT FOOD — Meal plan generator.

Generates a structured meal plan JSON based on calculated KBJU targets.
Uses OpenRouter API (Gemini 3 Flash).
"""

from __future__ import annotations

import json

import structlog
from openai import AsyncOpenAI

from config.settings import settings

logger = structlog.get_logger()

SYSTEM_PROMPT_TEMPLATE = """# ROLE
Ты — нутрициолог-технолог. Твоя задача — составить меню в формате JSON.

# INPUT DATA
Цель: {calories} ккал
Белки: {protein}
Жиры: {fats}
Углеводы: {carbs}
Исключить: {excluded_foods}
Аллергии: {allergies}

# STRICT RULES
1. Выводи ТОЛЬКО валидный JSON.
2. Если в "Исключить" или "Аллергии" есть продукт, он СТРОГО запрещен во всех блюдах.

# INSTRUCTIONS
1. **Структура:** СТРОГО 3 приема пищи: Завтрак, Обед, Ужин.
2. **Запрет:** НИКАКИХ перекусов, полдников или вторых завтраков. Даже если калорий очень много (3000+), увеличивай порции в основных блюдах, но не добавляй новые приемы пищи.
3. **Адаптация:** Используй продукты, доступные в масс-маркете.
4. **Фильтр:** Исключи аллергены и нелюбимые продукты (из списка INPUT DATA).

# OUTPUT JSON FORMAT
{{
  "meals": [
    {{
      "name": "Завтрак",
      "dish": "Омлет",
      "ingredients": [
        {{"name": "Яйцо", "weight_g": 100, "cals": 150, "p": 12, "f": 10, "c": 1}},
        {{"name": "Молоко", "weight_g": 50, "cals": 30, "p": 1, "f": 1, "c": 2}}
      ],
      "total_cals": 180
    }}
  ]
}}"""

USER_PROMPT = "Составь план питания на день, основываясь на КБЖУ и ограничениях, указанных в системной инструкции."


def _build_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
    )


async def run_agent_food(
    calories: int,
    protein: int,
    fats: int,
    carbs: int,
    excluded_foods: str = "none",
    allergies: str = "none",
) -> dict:
    """Generate a meal plan using AI.

    Args:
        calories, protein, fats, carbs: target macros
        excluded_foods: comma-separated list of foods to exclude
        allergies: comma-separated list of allergies

    Returns:
        Parsed meal plan dict with 'meals' key
    """
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        calories=calories,
        protein=protein,
        fats=fats,
        carbs=carbs,
        excluded_foods=excluded_foods,
        allergies=allergies,
    )

    logger.debug(
        "agent_food_request",
        calories=calories, protein=protein, fats=fats, carbs=carbs,
        excluded=excluded_foods, allergies=allergies,
    )

    client = _build_client()
    response = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": USER_PROMPT},
        ],
    )

    output = response.choices[0].message.content or ""

    logger.debug(
        "agent_food_response",
        output_len=len(output),
        tokens=response.usage.total_tokens if response.usage else None,
    )

    # Extract JSON from output
    try:
        # Try direct parse
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    # Try to extract from code blocks
    import re
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", output)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON
    match = re.search(r"(\{[\s\S]*\})", output)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    logger.error("agent_food_json_parse_failed", output=output[:500])
    return {"meals": [], "error": "Failed to parse meal plan"}
