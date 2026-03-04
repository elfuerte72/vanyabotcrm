# Проблемы локализации бота — требуют исправления

**Обнаружено:** 2026-03-04 (тестирование 197 тестов, ветка `test/comprehensive-bot-testing`)

---

## Сводная таблица

| # | Проблема | Серьёзность | Файл | Затронуты |
|---|---------|-------------|------|-----------|
| 1 | Заголовки плана питания hardcoded RU | **Средняя** | `formatter.py` | EN, AR |
| 2 | AI Food промпт на русском | **Средняя** | `ai_food.py` | EN, AR |
| 3 | Единый payment URL (Tribute) | **Средняя** | `callbacks.py` | EN, AR |
| 4 | "Считаю калории..." на всех языках сразу | Низкая | `message.py` | Все |
| 5 | Ошибки только на английском | Низкая | `message.py`, `callbacks.py` | RU, AR |
| 6 | /start не определяет язык | Низкая | `start.py` | Все |

---

## Проблема #1: Заголовки плана питания hardcoded на русском

**Серьёзность:** Средняя
**Файл:** `bot/src/services/formatter.py:125-134`

### Что происходит

Функция `format_meal_plan_html()` содержит захардкоженные русские строки. EN и AR пользователи получают план питания с русскими заголовками.

### Текущий код

```python
# bot/src/services/formatter.py:125-134
msg = "🍽 <b>ПЛАН ПИТАНИЯ ГОТОВ!</b>\n\n"
msg += "📊 <b>ИТОГО ЗА ДЕНЬ:</b>\n"
msg += f"🔥 Калории: <b>{calculated_stats['calories']}</b> / {target_stats.get('calories', 0)} ккал\n"
msg += f"🥩 Белки: <b>{calculated_stats['protein']}г</b> / {target_stats.get('protein', 0)}г\n"
msg += f"🧈 Жиры: <b>{calculated_stats['fats']}г</b> / {target_stats.get('fats', 0)}г\n"
msg += f"🍞 Углеводы: <b>{calculated_stats['carbs']}г</b> / {target_stats.get('carbs', 0)}г\n"
```

### Как исправить

1. Добавить строки в `src/i18n/en.py` и `src/i18n/ar.py`:

```python
# en.py
MEAL_PLAN_READY = "🍽 <b>YOUR MEAL PLAN IS READY!</b>"
DAILY_TOTAL = "📊 <b>DAILY TOTAL:</b>"
CALORIES_LABEL = "🔥 Calories"
PROTEIN_LABEL = "🥩 Protein"
FATS_LABEL = "🧈 Fats"
CARBS_LABEL = "🍞 Carbs"
KCAL = "kcal"

# ar.py
MEAL_PLAN_READY = "🍽 <b>!خطة الوجبات جاهزة</b>"
DAILY_TOTAL = "📊 <b>:المجموع اليومي</b>"
CALORIES_LABEL = "🔥 سعرات"
PROTEIN_LABEL = "🥩 بروتين"
FATS_LABEL = "🧈 دهون"
CARBS_LABEL = "🍞 كربوهيدرات"
KCAL = "سعرة"
```

2. Передавать `language` в `format_meal_plan_html()`:

```python
def format_meal_plan_html(menu_data, calculated_stats, target_stats, language="ru"):
    strings = get_strings(language)
    msg = f"{strings.MEAL_PLAN_READY}\n\n"
    msg += f"{strings.DAILY_TOTAL}\n"
    msg += f"{strings.CALORIES_LABEL}: <b>{calculated_stats['calories']}</b> / {target_stats.get('calories', 0)} {strings.KCAL}\n"
    # ...
```

---

## Проблема #2: AI Food промпт на русском

**Серьёзность:** Средняя
**Файл:** `bot/src/services/ai_food.py:18-44`

### Что происходит

Системный промпт для AI генерации плана питания написан на русском (`"Ты — нутрициолог-технолог..."`). Названия приёмов пищи и блюд в JSON тоже задаются на русском (`"Завтрак"`, `"Омлет"`). В результате EN/AR пользователи получают план с русскими названиями блюд.

### Текущий код

```python
# bot/src/services/ai_food.py:18-44
SYSTEM_PROMPT_TEMPLATE = """# ROLE
Ты — нутрициолог-технолог. Твоя задача — составить меню в формате JSON.
...
# OUTPUT JSON FORMAT
{{
  "meals": [
    {{
      "name": "Завтрак",
      "dish": "Омлет",
      ...
```

### Как исправить

1. Создать промпты на каждом языке:

```python
FOOD_PROMPTS = {
    "ru": """# ROLE
Ты — нутрициолог-технолог. Твоя задача — составить меню в формате JSON.
...
      "name": "Завтрак",
""",
    "en": """# ROLE
You are a nutritionist. Your task is to create a meal plan in JSON format.
...
      "name": "Breakfast",
""",
    "ar": """# ROLE
أنت أخصائي تغذية. مهمتك هي إنشاء خطة وجبات بتنسيق JSON.
...
      "name": "فطور",
""",
}
```

2. Принимать `language` в `run_agent_food()`:

```python
async def run_agent_food(calories, protein, fats, carbs, excluded, allergies, language="ru"):
    system_prompt = FOOD_PROMPTS[language].format(
        calories=calories, protein=protein, fats=fats, carbs=carbs,
        excluded_foods=excluded or "нет", allergies=allergies or "нет"
    )
```

---

## Проблема #3: Единый payment URL для всех языков

**Серьёзность:** Средняя
**Файл:** `bot/src/handlers/callbacks.py:28-33`

### Что происходит

`_get_payment_url()` возвращает один и тот же `settings.tribute_link` для всех языков. EN/AR пользователи платят в рублях (990₽ через Tribute) вместо долларов ($15 через Ziina).

### Текущий код

```python
# bot/src/handlers/callbacks.py:28-33
def _get_payment_url(language: str) -> str:
    """Get payment URL based on language (Tribute for RU, Ziina for EN/AR)."""
    if language == "ru":
        return settings.tribute_link
    # EN/AR use Ziina — for now same Tribute link, customize later
    return settings.tribute_link  # <-- BUG: должен быть ziina_link
```

### Как исправить

1. Добавить `ZIINA_LINK` в `config/settings.py`:

```python
class Settings(BaseSettings):
    ziina_link: str = ""  # Ziina payment link for EN/AR users
```

2. Исправить `_get_payment_url()`:

```python
def _get_payment_url(language: str) -> str:
    if language == "ru":
        return settings.tribute_link
    return settings.ziina_link or settings.tribute_link  # fallback на Tribute
```

3. Добавить env-переменную `ZIINA_LINK` в Railway.

---

## Проблема #4: "Считаю калории..." на всех языках сразу

**Серьёзность:** Низкая
**Файл:** `bot/src/handlers/message.py:148-155`

### Что происходит

Когда бот начинает считать КБЖУ, он отправляет сообщение на ВСЕХ 3 языках одновременно вместо языка пользователя.

### Текущий код

```python
# bot/src/handlers/message.py:148-155
strings = get_strings(detected_lang)  # определил язык, но не использует
await message.answer(
    f"<b>RU:</b>\n{get_strings('ru').CALCULATING_MENU}\n\n"
    f"<b>EN:</b>\n{get_strings('en').CALCULATING_MENU}\n\n"
    f"<b>AR:</b>\n{get_strings('ar').CALCULATING_MENU}",
    parse_mode="HTML",
)
```

### Как исправить

```python
strings = get_strings(detected_lang)
await message.answer(strings.CALCULATING_MENU, parse_mode="HTML")
```

Одна строка вместо трёх — `detected_lang` уже определён выше.

---

## Проблема #5: Сообщения об ошибках только на английском

**Серьёзность:** Низкая
**Файлы:**
- `bot/src/handlers/message.py:68`
- `bot/src/handlers/callbacks.py:66`

### Что происходит

Fallback-сообщения при ошибках захардкожены на английском:

```python
# message.py:68
await message.answer("Sorry, I couldn't process your voice message. Please type your answer.")

# callbacks.py:66
await bot.send_message(chat_id, "Sorry, video is temporarily unavailable.")
```

RU и AR пользователи получают английские ошибки.

### Как исправить

1. Добавить строки в i18n модули:

```python
# ru.py
VOICE_ERROR = "Извини, не удалось обработать голосовое сообщение. Пожалуйста, напиши текстом."
VIDEO_UNAVAILABLE = "Извини, видео временно недоступно."

# en.py
VOICE_ERROR = "Sorry, I couldn't process your voice message. Please type your answer."
VIDEO_UNAVAILABLE = "Sorry, video is temporarily unavailable."

# ar.py
VOICE_ERROR = "عذراً، لم أتمكن من معالجة رسالتك الصوتية. يرجى الكتابة."
VIDEO_UNAVAILABLE = "عذراً، الفيديو غير متوفر حالياً."
```

2. Использовать `get_strings(lang)` в обработчиках:

```python
# message.py:68
strings = get_strings(detected_lang or "en")
await message.answer(strings.VOICE_ERROR)

# callbacks.py:66 — нужно определить язык пользователя
language = await get_user_language(callback.from_user.id) or "en"
await bot.send_message(chat_id, get_strings(language).VIDEO_UNAVAILABLE)
```

---

## Проблема #6: /start не определяет язык

**Серьёзность:** Низкая
**Файл:** `bot/src/handlers/start.py`

### Что происходит

Приветствие отправляется как комбинация RU+EN+AR в одном сообщении. Бот не определяет язык пользователя.

### Текущий код

```python
# bot/src/handlers/start.py:11-20
@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "<b>RU:</b>\nПривет! Я помогу тебе рассчитать КБЖУ...\n\n"
        "<b>EN:</b>\nHi! I'll help you calculate your macros...\n\n"
        "<b>AR:</b>\nمرحباً! سأساعدك في حساب الماكروز...",
        parse_mode="HTML",
    )
```

### Как исправить

```python
from src.i18n import get_strings

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    # Telegram предоставляет language_code пользователя
    tg_lang = message.from_user.language_code or ""
    if tg_lang.startswith("ar"):
        lang = "ar"
    elif tg_lang.startswith("ru"):
        lang = "ru"
    else:
        lang = "en"

    strings = get_strings(lang)
    await message.answer(strings.START_MESSAGE, parse_mode="HTML")
```

Также добавить `START_MESSAGE` в i18n модули:

```python
# ru.py
START_MESSAGE = "Привет! Я помогу тебе рассчитать КБЖУ и составить план питания. Просто напиши мне!"

# en.py
START_MESSAGE = "Hi! I'll help you calculate your macros and create a nutrition plan. Just write to me!"

# ar.py
START_MESSAGE = "مرحباً! سأساعدك في حساب الماكروز وإنشاء خطة تغذية. فقط اكتب لي!"
```

---

## Порядок исправления (рекомендация)

### Приоритет 1 — средняя серьёзность, быстрый fix

1. **#4** — "Считаю..." на одном языке (1 строка кода)
2. **#3** — Payment URL (добавить `ZIINA_LINK` env + 1 строка)
3. **#5** — Ошибки на языке пользователя (добавить 4 строки в i18n)

### Приоритет 2 — средняя серьёзность, больше работы

4. **#1** — Заголовки плана питания (i18n + рефакторинг formatter)
5. **#6** — /start с определением языка (i18n + Telegram language_code)

### Приоритет 3 — большой объём работы

6. **#2** — AI Food промпт (3 промпта по ~30 строк + тестирование качества генерации)
