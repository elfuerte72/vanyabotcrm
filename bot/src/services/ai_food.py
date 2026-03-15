"""AGENT FOOD — Meal plan generator.

Generates a structured meal plan JSON based on calculated KBJU targets.
Uses OpenRouter API (Gemini 3 Flash).
"""

from __future__ import annotations

import json
import re

import structlog

from config.settings import settings
from src.services.ai_client import get_ai_client

logger = structlog.get_logger()

SYSTEM_PROMPTS = {
    "ru": """# ROLE
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
}}""",

    "en": """# ROLE
You are a nutritionist. Your task is to create a meal plan in JSON format.

# INPUT DATA
Target: {calories} kcal
Protein: {protein}
Fats: {fats}
Carbs: {carbs}
Exclude: {excluded_foods}
Allergies: {allergies}

# STRICT RULES
1. Output ONLY valid JSON.
2. If a food is listed in "Exclude" or "Allergies", it is STRICTLY forbidden in all dishes.

# INSTRUCTIONS
1. **Structure:** STRICTLY 3 meals: Breakfast, Lunch, Dinner.
2. **No snacks:** NO snacks or second breakfasts. Even if calories are very high (3000+), increase portions in main meals but do not add new meals.
3. **Adaptation:** Use products available in regular grocery stores.
4. **Filter:** Exclude allergens and disliked foods (from INPUT DATA).

# OUTPUT JSON FORMAT
{{
  "meals": [
    {{
      "name": "Breakfast",
      "dish": "Omelet",
      "ingredients": [
        {{"name": "Egg", "weight_g": 100, "cals": 150, "p": 12, "f": 10, "c": 1}},
        {{"name": "Milk", "weight_g": 50, "cals": 30, "p": 1, "f": 1, "c": 2}}
      ],
      "total_cals": 180
    }}
  ]
}}""",

    "ar": """# ROLE
أنت أخصائي تغذية. مهمتك هي إنشاء خطة وجبات بتنسيق JSON.

# INPUT DATA
الهدف: {calories} سعرة
بروتين: {protein}
دهون: {fats}
كربوهيدرات: {carbs}
استبعاد: {excluded_foods}
حساسية: {allergies}

# STRICT RULES
1. أخرج فقط JSON صالح.
2. إذا كان طعام مدرجاً في "استبعاد" أو "حساسية"، فهو ممنوع تماماً في جميع الأطباق.

# INSTRUCTIONS
1. **الهيكل:** 3 وجبات بالضبط: فطور، غداء، عشاء.
2. **ممنوع:** لا وجبات خفيفة. حتى لو كانت السعرات عالية جداً (3000+)، زد الحصص في الوجبات الرئيسية.
3. **التكيف:** استخدم منتجات متوفرة في المتاجر العادية.
4. **الفلتر:** استبعد مسببات الحساسية والأطعمة غير المرغوبة.

# OUTPUT JSON FORMAT
{{
  "meals": [
    {{
      "name": "فطور",
      "dish": "عجة",
      "ingredients": [
        {{"name": "بيض", "weight_g": 100, "cals": 150, "p": 12, "f": 10, "c": 1}},
        {{"name": "حليب", "weight_g": 50, "cals": 30, "p": 1, "f": 1, "c": 2}}
      ],
      "total_cals": 180
    }}
  ]
}}""",
}

USER_PROMPTS = {
    "ru": "Составь план питания на день, основываясь на КБЖУ и ограничениях, указанных в системной инструкции.",
    "en": "Create a daily meal plan based on the macros and restrictions specified in the system instructions.",
    "ar": "أنشئ خطة وجبات يومية بناءً على الماكروز والقيود المحددة في تعليمات النظام.",
}


async def run_agent_food(
    calories: int,
    protein: int,
    fats: int,
    carbs: int,
    excluded_foods: str = "none",
    allergies: str = "none",
    language: str = "ru",
) -> dict:
    """Generate a meal plan using AI.

    Args:
        calories, protein, fats, carbs: target macros
        excluded_foods: comma-separated list of foods to exclude
        allergies: comma-separated list of allergies
        language: language for prompt and meal names (ru/en/ar)

    Returns:
        Parsed meal plan dict with 'meals' key
    """
    template = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])
    system_prompt = template.format(
        calories=calories,
        protein=protein,
        fats=fats,
        carbs=carbs,
        excluded_foods=excluded_foods,
        allergies=allergies,
    )
    user_prompt = USER_PROMPTS.get(language, USER_PROMPTS["en"])

    logger.info(
        "agent_food_request",
        calories=calories, protein=protein, fats=fats, carbs=carbs,
        excluded=excluded_foods, allergies=allergies, language=language,
    )

    client = get_ai_client()

    max_retries = 2
    output = ""
    total_tokens = None

    for attempt in range(max_retries):
        response = await client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        message = response.choices[0]
        output = message.message.content or ""
        total_tokens = response.usage.total_tokens if response.usage else None

        if output.strip():
            break

        logger.warning(
            "agent_food_empty_response",
            attempt=attempt + 1,
            finish_reason=message.finish_reason,
            refusal=getattr(message.message, "refusal", None),
            tokens=total_tokens,
            language=language,
        )

    logger.info(
        "agent_food_response",
        output_len=len(output),
        tokens=total_tokens,
        language=language,
    )

    # Extract JSON from output
    try:
        # Try direct parse
        return json.loads(output)
    except json.JSONDecodeError:
        pass

    # Try to extract from code blocks
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

    logger.error("agent_food_json_parse_failed", output=output[:500], language=language)
    return {"meals": [], "error": "Failed to parse meal plan"}
