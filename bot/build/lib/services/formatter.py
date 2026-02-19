"""Format AI agent responses for Telegram.

Handles:
1. JSON extraction from agent output (is_finished detection)
2. Markdown → HTML conversion for Telegram
3. Meal plan JSON → HTML rendering
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class AgentResponse:
    """Parsed response from AGENT MAIN."""
    route_type: str  # 'conversation' or 'generate'
    text_response: str  # cleaned text for conversation
    data: dict[str, Any] | None = None  # parsed JSON for generate


def parse_agent_output(output: str) -> AgentResponse:
    """Parse AI agent output, extract JSON if present.

    Port of n8n 'new_formater' Code node.
    """
    parsed_data = None
    is_ready_to_generate = False
    clean_text = output

    # Try to find JSON in ```json ... ``` blocks first
    json_match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", output, re.IGNORECASE)

    # Fallback: find raw JSON object
    if not json_match:
        json_match = re.search(r"(\{[\s\S]*\})", output)

    if json_match:
        json_string = json_match.group(1)
        full_match = json_match.group(0)

        try:
            data = json.loads(json_string)
            parsed_data = data

            if data.get("is_finished") is True:
                is_ready_to_generate = True

            # Remove JSON from text
            clean_text = clean_text.replace(full_match, "")

            # Remove garbage phrases
            for pattern in [
                r"Here is the JSON:?",
                r"JSON output:?",
                r"System output:?",
                r"Вот json:?",
                r"Технические данные:?",
            ]:
                clean_text = re.sub(pattern, "", clean_text, flags=re.IGNORECASE)
        except json.JSONDecodeError:
            logger.warning("json_parse_failed", raw=json_string[:200])

    clean_text = clean_text.strip()

    if is_ready_to_generate:
        return AgentResponse(
            route_type="generate",
            text_response="",
            data=parsed_data,
        )

    # Convert markdown to Telegram HTML
    html_text = markdown_to_telegram_html(clean_text) if clean_text else ""

    return AgentResponse(
        route_type="conversation",
        text_response=html_text,
        data=parsed_data,
    )


def markdown_to_telegram_html(text: str) -> str:
    """Convert markdown-style formatting to Telegram HTML.

    Port of n8n 'new_formater' Code node logic.
    """
    # Bold: **text** → <b>text</b>
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    # Bold: __text__ → <b>text</b>
    text = re.sub(r"__(.*?)__", r"<b>\1</b>", text)

    # Lists: * item → bullet
    text = re.sub(r"^\*\s", "- ", text, flags=re.MULTILINE)

    # Italic: *text* → <i>text</i> (after bold replacement)
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)

    # Replace <br> with newline (before sanitize)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # Sanitize remaining < that aren't allowed HTML tags
    text = re.sub(r"<(?!/?(b|i|u|s|pre|code|a)(>|\s))", "&lt;", text)

    return text


def format_meal_plan_html(
    menu_data: dict[str, Any],
    calculated_stats: dict[str, Any],
    target_stats: dict[str, Any],
) -> str:
    """Format meal plan JSON into Telegram HTML.

    Port of n8n 'comver to HTML' Code node.
    """
    msg = "🍽 <b>ПЛАН ПИТАНИЯ ГОТОВ!</b>\n\n"

    if calculated_stats.get("calories", 0) == 0:
        msg += "<i>(Не удалось рассчитать итоги автоматически)</i>\n\n"
    else:
        msg += "📊 <b>ИТОГО ЗА ДЕНЬ:</b>\n"
        msg += f"🔥 Калории: <b>{calculated_stats['calories']}</b> / {target_stats.get('calories', 0)} ккал\n"
        msg += f"🥩 Белки: <b>{calculated_stats['protein']}г</b> / {target_stats.get('protein', 0)}г\n"
        msg += f"🧈 Жиры: <b>{calculated_stats['fats']}г</b> / {target_stats.get('fats', 0)}г\n"
        msg += f"🍞 Углеводы: <b>{calculated_stats['carbs']}г</b> / {target_stats.get('carbs', 0)}г\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    meals = menu_data.get("meals", [])
    for meal in meals:
        name = (meal.get("name") or "Приём пищи").upper()
        dish = meal.get("dish", "")

        # Icon based on meal name
        name_lower = name.lower()
        if any(w in name_lower for w in ("завтрак", "breakfast", "فطور")):
            icon = "🍳"
        elif any(w in name_lower for w in ("обед", "lunch", "غداء")):
            icon = "🍲"
        elif any(w in name_lower for w in ("ужин", "dinner", "عشاء")):
            icon = "🥗"
        elif any(w in name_lower for w in ("перекус", "snack")):
            icon = "🥜"
        else:
            icon = "🍽"

        msg += f"{icon} <b>{name}</b>\n"
        if dish:
            msg += f"<i>{dish}</i>\n\n"

        for ing in meal.get("ingredients", []):
            if isinstance(ing, str):
                msg += f"  • {ing}\n"
            else:
                name_str = ing.get("name", "?")
                weight = ing.get("weight_g", "?")
                cals = ing.get("cals", 0)
                msg += f"  • {name_str} — <b>{weight}г</b>"
                if cals:
                    msg += f" ({cals} ккал)"
                msg += "\n"

        total_cals = round(meal.get("total_cals", 0))
        if total_cals > 0:
            msg += f"\n  📌 <i>Итого: ~{total_cals} ккал</i>\n\n"
        else:
            msg += "\n"

    return msg


def validate_meal_plan(
    menu_data: dict[str, Any],
    target_calories: int,
    excluded_foods: str,
) -> tuple[bool, str | None, dict[str, int]]:
    """Validate generated meal plan.

    Port of n8n 'output -> json' Code node.

    Returns:
        (is_valid, error_reason, calculated_stats)
    """
    meals = menu_data.get("meals", [])
    if not meals:
        return False, "No meals in plan", {"calories": 0, "protein": 0, "fats": 0, "carbs": 0}

    total = {"calories": 0, "protein": 0, "fats": 0, "carbs": 0}

    for meal in meals:
        for ing in meal.get("ingredients", []):
            if isinstance(ing, dict):
                total["calories"] += ing.get("cals", 0)
                total["protein"] += ing.get("p", 0)
                total["fats"] += ing.get("f", 0)
                total["carbs"] += ing.get("c", 0)

    # Check excluded foods
    if excluded_foods and excluded_foods.lower() not in ("none", "нет", "no", "لا"):
        forbidden = [f.strip().lower() for f in excluded_foods.split(",")]
        for meal in meals:
            for ing in meal.get("ingredients", []):
                ing_name = (ing.get("name", "") if isinstance(ing, dict) else str(ing)).lower()
                for f in forbidden:
                    if f in ing_name:
                        return False, f"Forbidden food found: {f}", total

    # Check calorie tolerance (10%)
    if target_calories > 0:
        diff = abs(total["calories"] - target_calories)
        if diff > target_calories * 0.10:
            return False, f"Calories off target. Goal: {target_calories}, Got: {total['calories']}", total

    total = {k: round(v) for k, v in total.items()}
    return True, None, total
