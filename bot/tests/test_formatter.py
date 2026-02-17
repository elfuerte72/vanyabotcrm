"""Tests for formatter: parse_agent_output, markdown_to_telegram_html, validate_meal_plan."""

from src.services.formatter import (
    AgentResponse,
    format_meal_plan_html,
    markdown_to_telegram_html,
    parse_agent_output,
    validate_meal_plan,
)


class TestParseAgentOutput:
    def test_plain_text_conversation(self):
        result = parse_agent_output("Tell me your age please.")
        assert result.route_type == "conversation"
        assert "age" in result.text_response

    def test_json_code_block_generate(self):
        output = (
            'Here is the data:\n```json\n{"is_finished": true, "sex": "male", '
            '"weight": 80, "height": 180, "age": 30}\n```'
        )
        result = parse_agent_output(output)
        assert result.route_type == "generate"
        assert result.data is not None
        assert result.data["sex"] == "male"
        assert result.data["weight"] == 80

    def test_raw_json_generate(self):
        output = 'OK done! {"is_finished": true, "sex": "female", "weight": 60}'
        result = parse_agent_output(output)
        assert result.route_type == "generate"
        assert result.data["sex"] == "female"

    def test_json_not_finished_stays_conversation(self):
        output = '{"is_finished": false, "sex": "male"}'
        result = parse_agent_output(output)
        assert result.route_type == "conversation"
        assert result.data is not None

    def test_invalid_json_stays_conversation(self):
        output = "Here is {broken json: without end"
        result = parse_agent_output(output)
        assert result.route_type == "conversation"

    def test_garbage_phrases_removed(self):
        output = 'Here is the JSON:\n{"is_finished": true, "sex": "male"}'
        result = parse_agent_output(output)
        assert "Here is the JSON" not in result.text_response

    def test_empty_output(self):
        result = parse_agent_output("")
        assert result.route_type == "conversation"
        assert result.text_response == ""


class TestMarkdownToTelegramHtml:
    def test_bold_double_asterisk(self):
        assert markdown_to_telegram_html("**hello**") == "<b>hello</b>"

    def test_bold_double_underscore(self):
        assert markdown_to_telegram_html("__hello__") == "<b>hello</b>"

    def test_italic_single_asterisk(self):
        assert markdown_to_telegram_html("*hello*") == "<i>hello</i>"

    def test_bold_before_italic(self):
        result = markdown_to_telegram_html("**bold** and *italic*")
        assert "<b>bold</b>" in result
        assert "<i>italic</i>" in result

    def test_list_bullet(self):
        result = markdown_to_telegram_html("* item one\n* item two")
        assert "- item one" in result
        assert "- item two" in result

    def test_sanitize_unknown_html_tags(self):
        result = markdown_to_telegram_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script" in result

    def test_allowed_tags_preserved(self):
        result = markdown_to_telegram_html("<b>bold</b> <i>italic</i>")
        assert "<b>bold</b>" in result
        assert "<i>italic</i>" in result

    def test_br_to_newline(self):
        result = markdown_to_telegram_html("line1<br>line2")
        assert "line1\nline2" in result


class TestValidateMealPlan:
    def test_valid_plan(self, sample_meal_plan):
        is_valid, error, stats = validate_meal_plan(sample_meal_plan, 1300, "none")
        assert is_valid is True
        assert error is None
        assert stats["calories"] > 0

    def test_empty_meals(self):
        is_valid, error, stats = validate_meal_plan({"meals": []}, 2000, "none")
        assert is_valid is False
        assert "No meals" in error

    def test_no_meals_key(self):
        is_valid, error, stats = validate_meal_plan({}, 2000, "none")
        assert is_valid is False

    def test_forbidden_food_detected(self, sample_meal_plan):
        is_valid, error, stats = validate_meal_plan(sample_meal_plan, 2000, "Тунец")
        assert is_valid is False
        assert "тунец" in error.lower()

    def test_calorie_tolerance_exceeded(self, sample_meal_plan):
        # Plan has ~1313 cals; target 3000 → way off
        is_valid, error, stats = validate_meal_plan(sample_meal_plan, 3000, "none")
        assert is_valid is False
        assert "off target" in error.lower()

    def test_calorie_tolerance_within_10_percent(self, sample_meal_plan):
        # Total cals from sample fixture: 280+57+48+330+280+180+50+88 = 1313
        is_valid, error, stats = validate_meal_plan(sample_meal_plan, 1313, "none")
        assert is_valid is True

    def test_none_excluded_foods(self, sample_meal_plan):
        is_valid, _, _ = validate_meal_plan(sample_meal_plan, 1313, "none")
        assert is_valid is True

    def test_russian_none_excluded(self, sample_meal_plan):
        is_valid, _, _ = validate_meal_plan(sample_meal_plan, 1313, "нет")
        assert is_valid is True

    def test_string_ingredients_handled(self):
        plan = {
            "meals": [
                {
                    "name": "Lunch",
                    "dish": "Salad",
                    "total_cals": 300,
                    "ingredients": ["lettuce", "tomato"],
                }
            ]
        }
        is_valid, _, stats = validate_meal_plan(plan, 300, "none")
        # String ingredients have no cals → 0 total → calorie off target
        assert stats["calories"] == 0


class TestFormatMealPlanHtml:
    def test_contains_meal_names(self, sample_meal_plan):
        stats = {"calories": 1300, "protein": 100, "fats": 20, "carbs": 140}
        target = {"calories": 1300, "protein": 100, "fats": 20, "carbs": 140}
        html = format_meal_plan_html(sample_meal_plan, stats, target)
        assert "ЗАВТРАК" in html
        assert "ОБЕД" in html
        assert "УЖИН" in html

    def test_contains_ingredients(self, sample_meal_plan):
        stats = {"calories": 1300, "protein": 100, "fats": 20, "carbs": 140}
        target = {"calories": 1300, "protein": 100, "fats": 20, "carbs": 140}
        html = format_meal_plan_html(sample_meal_plan, stats, target)
        assert "Куриная грудка" in html
        assert "200г" in html

    def test_zero_calories_shows_fallback(self, sample_meal_plan):
        stats = {"calories": 0, "protein": 0, "fats": 0, "carbs": 0}
        target = {"calories": 0}
        html = format_meal_plan_html(sample_meal_plan, stats, target)
        assert "Не удалось рассчитать" in html

    def test_icons_present(self, sample_meal_plan):
        stats = {"calories": 1300, "protein": 100, "fats": 20, "carbs": 140}
        target = {"calories": 1300}
        html = format_meal_plan_html(sample_meal_plan, stats, target)
        assert "🍳" in html  # breakfast
        assert "🍲" in html  # lunch
        assert "🥗" in html  # dinner
