# Отчёт о тестировании Telegram-бота VanyaBot

**Дата:** 2026-03-04
**Ветка:** `test/comprehensive-bot-testing`
**Результат:** 197 тестов — все прошли (0 failures)
**Время выполнения:** ~2 мин 31 сек

---

## Содержание

1. [Обзор тестирования](#1-обзор-тестирования)
2. [КБЖУ Pipeline — как агент считает и сохраняет данные](#2-кбжу-pipeline)
3. [Запись в базу данных](#3-запись-в-базу-данных)
4. [Воронка продаж — симуляция 6 дней](#4-воронка-продаж)
5. [Callback-обработчики — как работают кнопки в Telegram](#5-callback-обработчики)
6. [Ответы бота по языкам — полный справочник](#6-ответы-бота-по-языкам)
7. [Обнаруженные проблемы и рекомендации](#7-обнаруженные-проблемы)
8. [Тестовая инфраструктура](#8-тестовая-инфраструктура)

---

## 1. Обзор тестирования

### Что тестировалось

| Область | Описание | Тестов |
|---------|----------|--------|
| КБЖУ Pipeline | Полный цикл: текст → AI агент → расчёт → запись в БД → генерация меню → отправка | 15 |
| Воронка продаж | Симуляция 6-дневного цикла × 3 языка, кнопки, тексты, ошибкоустойчивость | 71 |
| Callback-обработчики | 7 типов кнопок × 3 языка, обновление CRM, клавиатуры | 40 |
| База данных (integration) | Реальная PostgreSQL: upsert, воронка, покупатели, история чата | 19 |
| Калькулятор | Формула Mifflin-St Jeor, все цели и активности | 9 |
| Детекция языка | RU/EN/AR определение по Unicode блокам | 10 |
| i18n модули | Наличие всех строк, fallback на English | 3 |
| Funnel messages | Маппинг stage → текст + кнопки | 8 |
| Existing callbacks | Оригинальные callback-тесты | 22 |
| **Итого** | | **197** |

### Структура тестов

```
bot/tests/
├── conftest.py                  — Общие fixtures + multilingual helpers
├── helpers.py                   — Фабрики: make_user(), make_bot(), make_callback()
├── test_kbju_pipeline.py        — КБЖУ pipeline × RU/EN/AR (NEW)
├── test_funnel_simulation.py    — Воронка 6 дней × 3 языка (NEW)
├── test_callbacks_multilang.py  — Callbacks × 3 языка + CRM (NEW)
├── test_db_integration.py       — Integration с реальной БД (EXTENDED)
├── test_callbacks.py            — Оригинальные callback тесты
├── test_funnel.py               — Базовые funnel тесты
├── test_funnel_integration.py   — Funnel sender integration
├── test_calculator.py           — Калькулятор КБЖУ
├── test_calculator_extended.py  — Расширенные тесты калькулятора
├── test_formatter.py            — Форматирование HTML
├── test_language.py             — Детекция языка
├── test_i18n.py                 — Локализация
├── test_message_handler.py      — Обработчик сообщений
├── test_e2e_integration.py      — E2E с реальной БД
└── BOT_BEHAVIOR_SUMMARY.md      — Справочник поведения бота
```

---

## 2. КБЖУ Pipeline

### Как работает полный pipeline

```
Пользователь отправляет текст
         │
         ▼
detect_language(text) → определяет язык (RU/EN/AR)
         │
         ▼
run_agent_main(chat_id, text) → AI отвечает
         │
         ▼
parse_agent_output(response) → "conversation" или "generate"
         │
    ┌────┴────┐
    ▼         ▼
conversation  generate (is_finished=True)
 ↓              ↓
Отправить    calculate_macros() → MacroResult
текст        save_user_data() → INSERT/UPDATE в БД
             run_agent_food() → JSON план питания
             validate_meal_plan() → проверка калорий ±10%
             format_meal_plan_html() → HTML
             message.answer(html) → отправка пользователю
             set_food_received() → get_food=TRUE, funnel_stage=0
```

### Тестовые профили пользователей

| Профиль | Язык | Пол | Вес | Рост | Возраст | Активность | Цель |
|---------|------|-----|-----|------|---------|------------|------|
| Иван | RU | male | 80 кг | 180 см | 30 | moderate | weight_loss |
| Jane | EN | female | 60 кг | 165 см | 25 | light | maintenance |
| Ахмед | AR | male | 75 кг | 175 см | 28 | high | muscle_gain |

### Рассчитанные КБЖУ по формуле Mifflin-St Jeor

**Иван (RU) — male, 80 кг, 180 см, 30 лет, moderate, weight_loss:**
```
BMR = 10×80 + 6.25×180 - 5×30 + 5 = 800 + 1125 - 150 + 5 = 1780
TDEE = 1780 × 1.55 = 2759
Target = 2759 × 0.85 = 2345 ккал (weight_loss = -15%)
Белки: 80 × 1.5 = 120г (480 ккал)
Жиры: 80 × 1.0 = 80г (720 ккал)
Углеводы: (2345 - 480 - 720) / 4 = 286г
```

**Jane (EN) — female, 60 кг, 165 см, 25 лет, light, maintenance:**
```
BMR = 10×60 + 6.25×165 - 5×25 - 161 = 600 + 1031 - 125 - 161 = 1345
TDEE = 1345 × 1.375 = 1850
Target = 1850 × 1.0 = 1850 ккал (maintenance)
Белки: 60 × 1.4 = 84г (336 ккал)
Жиры: 60 × 1.0 = 60г (540 ккал)
Углеводы: (1850 - 336 - 540) / 4 = 244г
```

**Ахмед (AR) — male, 75 кг, 175 см, 28 лет, high, muscle_gain:**
```
BMR = 10×75 + 6.25×175 - 5×28 + 5 = 750 + 1094 - 140 + 5 = 1709
TDEE = 1709 × 1.725 = 2948
Target = 2948 × 1.10 = 3243 ккал (muscle_gain = +10%)
Белки: 75 × 1.5 = 112г (450 ккал)
Жиры: 75 × 1.0 = 75г (675 ккал)
Углеводы: (3243 - 450 - 675) / 4 = 530г
```

### Проведённые тесты КБЖУ pipeline

| Тест | Что проверяет | Результат |
|------|--------------|-----------|
| `test_kbju_pipeline_ru` | Полный pipeline на русском: agent → КБЖУ → save → food → send | PASSED |
| `test_kbju_pipeline_en` | Полный pipeline на английском | PASSED |
| `test_kbju_pipeline_ar` | Полный pipeline на арабском | PASSED |
| `test_macros_match_calculator[ru/en/ar]` | КБЖУ в БД совпадают с калькулятором | PASSED ×3 |
| `test_set_food_received_called_after_meal_plan_sent` | `set_food_received` вызывается ПОСЛЕ отправки меню | PASSED |
| `test_language_detected_and_saved_to_db[ru/en/ar]` | Кириллица→ru, Latin→en, Arabic→ar, сохраняется в БД | PASSED ×3 |
| `test_already_calculated_sends_block_message[ru/en/ar]` | Повторный запрос → ALREADY_CALCULATED на языке юзера | PASSED ×3 |
| `test_already_calculated_does_not_call_agent` | При get_food=TRUE AI агент НЕ вызывается | PASSED |
| `test_conversation_does_not_trigger_kbju` | Обычный ответ AI (без JSON) → нет расчёта КБЖУ | PASSED |

### Как бот отвечает в pipeline

**Шаг 1: Сбор данных (conversation route)**
Бот задаёт вопросы через AI агента (Gemini 3 Flash). Ответы на языке пользователя. Пример:
- RU: "Привет! Расскажи, какой у тебя рост и вес?"
- EN: "Hello! Tell me your height and weight, please."
- AR: "مرحبا! أخبرني عن طولك ووزنك من فضلك."

**Шаг 2: Данные собраны (generate route)**
AI отправляет JSON с `is_finished: true`. Бот:
1. Отправляет "Считаю..." (на ВСЕХ 3 языках одновременно — см. [проблема #4](#проблема-4-calculating-message))
2. Рассчитывает КБЖУ
3. Генерирует план питания
4. Отправляет HTML с планом (заголовки на русском — см. [проблема #1](#проблема-1-meal-plan-headers))

**Шаг 3: Блокировка повторных запросов**
- RU: "Чемпион, извини. Я не могу второй раз тебе рассчитать КБЖУ."
- EN: "Champion, I'm sorry. I cannot calculate your macros a second time."
- AR: "بطل، اعتذر منك. لا يمكنني حساب السعرات والماكروز لك مرة ثانية."

---

## 3. Запись в базу данных

### Integration тесты с реальной PostgreSQL

Тесты подключаются к реальной Railway PostgreSQL и используют зарезервированные `chat_id` (99990001-99990010). Cleanup выполняется перед и после каждого теста.

| Тест | SQL операция | Что проверяет | Результат |
|------|-------------|--------------|-----------|
| `test_save_and_get_user` | `INSERT INTO users_nutrition` | Все 15 полей записываются и читаются | PASSED |
| `test_save_user_data_upsert` | `ON CONFLICT DO UPDATE` | Повторный INSERT обновляет данные | PASSED |
| `test_save_user_data_resets_get_food` | `SET get_food = FALSE` | Re-save сбрасывает get_food (re-calculation) | PASSED |
| `test_get_user_not_found` | `SELECT WHERE chat_id = ...` | Несуществующий user → None | PASSED |
| `test_mark_as_buyer` | `UPDATE SET is_buyer = TRUE` | Покупатель помечается в БД | PASSED |
| `test_set_food_received` | `SET get_food=TRUE, funnel_stage=0` | Запуск воронки после отправки меню | PASSED |
| `test_get_funnel_targets` | `SELECT WHERE is_buyer IS NOT TRUE AND stage 0-4` | Покупатели и stage≥5 исключаются | PASSED |
| `test_update_funnel_stage` | `SET funnel_stage = funnel_stage + 1` | Безусловный инкремент 0→1→2 | PASSED |
| `test_advance_funnel_if_at_stage_matches` | `UPDATE WHERE funnel_stage = $2` | Условный инкремент (stage совпадает) | PASSED |
| `test_advance_funnel_if_at_stage_no_match` | `UPDATE WHERE funnel_stage = $2` | Не инкрементирует (stage не совпадает) | PASSED |
| `test_advance_funnel_if_at_stage_idempotent` | Повторный вызов | Второй вызов → False, stage не меняется | PASSED |
| `test_save_and_get_chat_history` | `INSERT/SELECT n8n_chat_histories` | JSONB сохранение, порядок oldest-first | PASSED |
| `test_get_chat_history_limit` | `ORDER BY id DESC LIMIT N` | Возвращает N последних сообщений | PASSED |
| `test_get_user_language` | `SELECT language` | Быстрый lookup языка пользователя | PASSED |

### Схема данных в PostgreSQL

```sql
-- Основная таблица пользователей
users_nutrition (
    chat_id BIGINT PRIMARY KEY,  -- Telegram ID
    username TEXT,
    first_name TEXT,
    sex TEXT,           -- male/female
    age INT,
    weight FLOAT,       -- кг
    height FLOAT,       -- см
    activity_level TEXT, -- sedentary/light/moderate/high/extreme
    goal TEXT,          -- weight_loss/maintenance/muscle_gain
    calories INT,       -- рассчитанные КБЖУ
    protein INT,
    fats INT,
    carbs INT,
    get_food BOOLEAN,   -- TRUE = меню получено, повторный расчёт заблокирован
    is_buyer BOOLEAN,   -- TRUE = оплатил тренировку
    funnel_stage INT,   -- 0-6, текущий день воронки
    language TEXT,       -- ru/en/ar
    last_funnel_msg_at TIMESTAMP  -- последнее сообщение воронки
)
```

### Ключевые SQL-поведения (подтверждены тестами)

1. **UPSERT**: `save_user_data` использует `ON CONFLICT (chat_id) DO UPDATE` — повторный расчёт обновляет данные и сбрасывает `get_food = FALSE`
2. **Воронка**: `set_food_received` устанавливает `funnel_stage = 0` и `get_food = TRUE` — пользователь попадает в воронку
3. **Покупатель**: `mark_as_buyer` ставит `is_buyer = TRUE` — пользователь исключается из `get_funnel_targets`
4. **Условный advance**: `advance_funnel_if_at_stage` инкрементирует ТОЛЬКО если текущий stage совпадает — защита от двойного инкремента

---

## 4. Воронка продаж

### Как работает воронка

```
Пользователь получает план питания
         │
         ▼
set_food_received() → funnel_stage=0, get_food=TRUE
         │
         ▼
Ежедневный cron (23:00 UTC) → send_funnel_messages(bot)
         │
         ▼
get_funnel_targets() → WHERE is_buyer IS NOT TRUE AND stage 0-4
         │
         ▼
Для каждого пользователя:
  1. get_funnel_message(stage, language) → текст + кнопки
  2. bot.send_message(text, inline_keyboard)
  3. update_funnel_stage(chat_id) → stage + 1
         │
    ┌────┴────────────────────────────────────┐
    ▼                                         ▼
Stage 0→1→2→3→4→5 (EXIT)          buy_now → is_buyer=TRUE (EXIT)
```

### Симуляция 6-дневного цикла

Тестировался полный 6-дневный цикл для каждого из 3 языков:

#### День 0 — "Разбуди тело"
**Что отправляет бот:**
- RU: Рассказ про "спящее тело", зарядка "Разбуди своё тело за 7 минут"
- EN: "Wake up your body in 7 minutes" — gentle activation
- AR: "أيقظ جسمك في 7 دقائق" — активация тела

**Кнопка:** `[Разбуди тело / Wake up your body / أيقظ جسمك]` → callback `video_workout`

#### День 1 — "Скидка"
**Что отправляет бот:**
- RU: "Тело включилось. Тренировка за ~~1900₽~~ → **990₽**"
- EN: "Body activated. Workout for ~~$25~~ → **$15**"
- AR: "الجسم تنشط. التمرين بـ ~~$25~~ → **$15**"

**Кнопка:** `[Купить со скидкой / Buy with discount / اشتري بخصم]` → callback `buy_now`

#### День 2 — "Социальное доказательство"
**Что отправляет бот:** Отзывы клиентов (отёки ушли, живот стал меньше, целлюлит уменьшился)

**Кнопки:**
1. `[Да, хочу результат! / Yes, I want results! / نعم، أريد نتائج!]` → `buy_now`
2. `[Тренировка подойдёт мне? / Will it suit me? / هل يناسبني؟]` → `check_suitability`

#### День 3 — "Боль → Решение"
**Что отправляет бот:** Проблемные зоны (отёки, ушки, живот) → тренировка 20 мин

**Кнопки:**
1. `[Да! / Yes! / نعم!]` → `buy_now`
2. `[Что в программе? / What's in the program? / ماذا في البرنامج؟]` → `show_info`

#### День 4 — "Цена"
**Что отправляет бот:** Сравнение цены (RU: 990₽ < ужин/тушь/кофейня, EN/AR: $15 < dinner/mascara/coffee)

**Кнопки:**
1. `[Хочу скидку / I want a discount / أريد خصماً]` → `buy_now`
2. `[Мне не подходит / Not for me / لا يناسبني]` → `none`

#### День 5 — "Мягкий дедлайн"
**Что отправляет бот:** Последний день скидки, список преимуществ

**Кнопки:**
1. `[Да, беру! / Yes, I'm in! / نعم، آخذه!]` → `buy_now`
2. `[Напомни позже / Remind me later / ذكرني لاحقاً]` → `remind_later`

### Проведённые тесты воронки

| Тест | Что проверяет | Результат |
|------|--------------|-----------|
| `test_full_cycle_ru/en/ar` | Полный 6-дневный цикл на каждом языке | PASSED ×3 |
| `test_funnel_text_matches_i18n[0-5 × ru/en/ar]` | Текст = i18n строка для каждого дня/языка | PASSED ×18 |
| `test_buttons_have_correct_callback_data[0-5 × ru/en/ar]` | callback_data кнопок корректны | PASSED ×18 |
| `test_button_labels_match_i18n[0-5 × ru/en/ar]` | Labels кнопок = i18n строки | PASSED ×18 |
| `test_stage_minus_1/6/100_returns_none` | Невалидные stage → None | PASSED ×3 |
| `test_stage_increments_after_each_send` | update_funnel_stage вызван ПОСЛЕ отправки | PASSED |
| `test_no_targets_means_no_sends` | Пустой список → ничего не отправляется | PASSED |
| `test_one_user_error_does_not_block_others` | Ошибка 1 пользователя → остальные получают | PASSED |
| `test_mixed_languages_get_correct_messages` | 3 пользователя с разными языками | PASSED |
| `test_mixed_stages_get_correct_day_messages` | Пользователи на разных stage | PASSED |
| `test_keyboard_buttons_sent_correctly[0-5]` | InlineKeyboard формируется правильно | PASSED ×6 |

### Ошибкоустойчивость воронки

Тест `test_one_user_error_does_not_block_others` подтвердил:
- 3 пользователя (RU/EN/AR) в очереди
- Отправка 2-му пользователю падает с ошибкой ("User blocked the bot")
- Пользователи 1 и 3 всё равно получают сообщения
- `update_funnel_stage` НЕ вызывается для упавшего пользователя

---

## 5. Callback-обработчики

### Как работают кнопки в Telegram

Бот использует 7 типов inline-кнопок. При нажатии Telegram отправляет `CallbackQuery` с полем `data`.

### Таблица всех callbacks и их действий

| Callback | Действие | Обновление CRM | Что отправляет бот |
|----------|----------|---------------|-------------------|
| `buy_now` | Помечает покупателем | `is_buyer = TRUE` | Текст оплаты + URL-кнопка Tribute |
| `show_info` | Скачивает видео из Google Drive | Нет | Видео "Что в программе" |
| `show_results` | Рандомное фото результатов | Нет | Фото + caption на языке юзера |
| `check_suitability` | Скачивает видео из Google Drive | Нет | Видео "Подойдёт ли мне" |
| `remind_later` | Ничего | Нет | Текст с ссылкой на канал |
| `none` | Ничего | Нет | Мотивационный текст + ссылка на канал |
| `video_workout` | Условный advance stage 1→2 | `funnel_stage +1 if stage=1` | Текст + видео URL + buy кнопка |

### Детали callback `buy_now`

```
Пользователь нажимает "Купить" / "Buy" / "ادفع"
         │
         ▼
get_user_language(user_id) → определяет язык
         │
         ▼
mark_as_buyer(user_id) → UPDATE is_buyer=TRUE
         │
         ▼
bot.send_message:
  text: BUY_MESSAGE (на языке юзера)
  reply_markup: InlineKeyboard
    └─ [💳 Оплатить / Pay / ادفع] → URL (settings.tribute_link)
         │
         ▼
callback.answer() → убирает "loading" spinner
```

**Ответ бота:**
- RU: "💳 Отлично! Переходи к оплате: 👇 Нажми на кнопку ниже..."
- EN: "💳 Great! Proceed to payment: 👇 Press the button below..."
- AR: "💳 ممتاز! انتقلي للدفع: 👇 اضغطي على الزر أدناه..."

### Детали callback `video_workout`

```
Пользователь нажимает "Разбуди тело" (из Day 0 воронки)
         │
         ▼
callback.answer() → немедленно (до логики)
         │
         ▼
get_user_language(user_id) → язык
         │
         ▼
bot.send_message:
  text: VIDEO_WORKOUT_RESPONSE (на языке юзера)
  reply_markup: InlineKeyboard
    ├─ Row 1: [▶️ Смотреть видео / Watch video / شاهد الفيديو] → URL
    └─ Row 2: [💳 Оплатить / Pay / ادفع] → callback "buy_now"
         │
         ▼
advance_funnel_if_at_stage(user_id, expected_stage=1)
  → Если stage=1: инкремент до 2 (scheduler уже поставил 1)
  → Если stage≠1: ничего не делает
```

### Проведённые тесты callbacks

| Тест | Что проверяет | Результат |
|------|--------------|-----------|
| `test_buy_now_text_per_language[ru/en/ar]` | BUY_MESSAGE на правильном языке | PASSED ×3 |
| `test_buy_now_marks_buyer_in_db[ru/en/ar]` | mark_as_buyer вызван с user_id | PASSED ×3 |
| `test_buy_now_keyboard_has_url_button[ru/en/ar]` | Кнопка = URL (не callback) | PASSED ×3 |
| `test_buy_now_none_language_defaults_en` | language=None → English | PASSED |
| `test_show_info_sends_video` | send_info_video вызван | PASSED |
| `test_show_info_error_sends_fallback` | При ошибке → "unavailable" | PASSED |
| `test_show_results_caption_per_language[ru/en/ar]` | RESULTS_CAPTION на языке | PASSED ×3 |
| `test_check_suitability_sends_video` | send_suitability_video вызван | PASSED |
| `test_remind_later_text_per_language[ru/en/ar]` | REMIND_LATER на языке | PASSED ×3 |
| `test_none_text_per_language[ru/en/ar]` | NONE_RESPONSE на языке | PASSED ×3 |
| `test_video_workout_text_per_language[ru/en/ar]` | VIDEO_WORKOUT_RESPONSE на языке | PASSED ×3 |
| `test_video_workout_advances_funnel[ru/en/ar]` | advance_funnel_if_at_stage(1) вызван | PASSED ×3 |
| `test_video_workout_keyboard_structure[ru/en/ar]` | 2 ряда: URL + buy_now callback | PASSED ×3 |
| `test_buy_now_sets_is_buyer_true` | CRM: is_buyer=TRUE | PASSED |
| `test_video_workout_advances_stage_1_to_2` | CRM: funnel_stage 1→2 | PASSED |
| `test_show_info_no_crm_update` | Нет CRM-изменений | PASSED |
| `test_remind_later_no_crm_update` | Нет CRM-изменений | PASSED |
| `test_none_no_crm_update` | Нет CRM-изменений | PASSED |

---

## 6. Ответы бота по языкам

### Цены и валюты

| | Русский | English | العربية |
|--|---------|---------|---------|
| Обычная цена | 1900₽ | $25 | $25 |
| Скидка | 990₽ | $15 | $15 |
| Сравнение с личной тренировкой | 1500-3000₽ | $30-50 | $30-50 |

### Тон обращения

| | Русский | English | العربية |
|--|---------|---------|---------|
| Обращение | Неформальное (ты) | Неформальное (you) | Полуформальное |
| Гендер | Женский (решила, внедрила) | Нейтральный/женский | Женский (قررت) |

### Полная карта кнопок воронки

```
Day 0: [video_workout]
         └─→ Ответ: VIDEO_WORKOUT_RESPONSE + [URL видео] + [buy_now]
              CRM: advance_funnel_if_at_stage(1)

Day 1: [buy_now]
         └─→ Ответ: BUY_MESSAGE + [URL оплаты]
              CRM: mark_as_buyer → is_buyer=TRUE

Day 2: [buy_now] [check_suitability]
         └─→ check_suitability: видео из Google Drive

Day 3: [buy_now] [show_info]
         └─→ show_info: видео из Google Drive

Day 4: [buy_now] [none]
         └─→ none: мотивационный текст + ссылка на канал

Day 5: [buy_now] [remind_later]
         └─→ remind_later: ободряющий текст + ссылка на канал
```

---

## 7. Обнаруженные проблемы

### Проблема #1: Заголовки плана питания на русском {#проблема-1-meal-plan-headers}

**Файл:** `bot/src/services/formatter.py:125-134`
**Серьёзность:** Средняя
**Описание:** Функция `format_meal_plan_html()` использует hardcoded русские строки:
- `"ПЛАН ПИТАНИЯ ГОТОВ!"` — всегда на русском, даже для EN/AR
- `"ИТОГО ЗА ДЕНЬ:"` — всегда на русском
- `"ккал"` — единица измерения на русском

**Влияние:** EN и AR пользователи получают план питания с русскими заголовками.

**Рекомендация:** Добавить в i18n модули:
```python
MEAL_PLAN_READY = "🍽 MEAL PLAN IS READY!"
DAILY_TOTAL = "📊 DAILY TOTAL:"
KCAL = "kcal"
SUBTOTAL = "Subtotal"
```
И передавать `language` параметр в `format_meal_plan_html()`.

---

### Проблема #2: AI Food промпт на русском {#проблема-2-ai-food-prompt}

**Файл:** `bot/src/services/ai_food.py`
**Серьёзность:** Средняя
**Описание:** Системный промпт для генерации плана питания написан на русском: `"Ты — нутрициолог-технолог..."`. Это значит, что названия блюд и ингредиентов будут на русском, даже если пользователь EN или AR.

**Влияние:** EN/AR пользователи получают план с русскими названиями блюд.

**Рекомендация:** Передавать `language` в `run_agent_food()` и использовать соответствующий промпт:
```python
async def run_agent_food(calories, protein, fats, carbs, excluded, allergies, language="en"):
    system_prompt = FOOD_PROMPTS[language]  # промпт на нужном языке
```

---

### Проблема #3: Сообщение об ошибках только на английском {#проблема-3-error-messages}

**Файлы:**
- `bot/src/handlers/message.py:68` — "Sorry, I couldn't process your voice message"
- `bot/src/handlers/callbacks.py:66` — "Sorry, video is temporarily unavailable"

**Серьёзность:** Низкая
**Описание:** Fallback-сообщения при ошибках всегда на английском.

**Рекомендация:** Добавить в i18n:
```python
VOICE_ERROR = "Извини, не удалось обработать голосовое сообщение."
VIDEO_UNAVAILABLE = "Видео временно недоступно."
```

---

### Проблема #4: Calculating message на всех языках {#проблема-4-calculating-message}

**Файл:** `bot/src/handlers/message.py:151-155`
**Серьёзность:** Низкая
**Описание:** Сообщение "Считаю калории..." отправляется на ВСЕХ 3 языках одновременно:
```python
f"<b>RU:</b>\n{get_strings('ru').CALCULATING_MENU}\n\n"
f"<b>EN:</b>\n{get_strings('en').CALCULATING_MENU}\n\n"
f"<b>AR:</b>\n{get_strings('ar').CALCULATING_MENU}"
```

**Рекомендация:** Отправлять только на обнаруженном языке:
```python
strings = get_strings(detected_lang)
await message.answer(strings.CALCULATING_MENU, parse_mode="HTML")
```

---

### Проблема #5: Единый payment URL для всех языков {#проблема-5-payment-url}

**Файл:** `bot/src/handlers/callbacks.py:28-33`
**Серьёзность:** Средняя
**Описание:** `_get_payment_url()` возвращает один и тот же `settings.tribute_link` для всех языков. EN/AR пользователи должны платить через Ziina ($15), а не Tribute (990₽).

**Рекомендация:**
```python
def _get_payment_url(language: str) -> str:
    if language == "ru":
        return settings.tribute_link  # 990₽
    return settings.ziina_link  # $15
```

---

### Проблема #6: /start не определяет язык {#проблема-6-start}

**Файл:** `bot/src/handlers/start.py`
**Серьёзность:** Низкая
**Описание:** Приветствие отправляется как комбинация RU+EN+AR в одном сообщении, без определения языка пользователя.

**Рекомендация:** Определять язык из `message.from_user.language_code` (Telegram предоставляет) и отправлять приветствие на нужном языке.

---

### Сводная таблица проблем

| # | Проблема | Серьёзность | Файл | Затронутые языки |
|---|---------|-------------|------|-----------------|
| 1 | Заголовки плана питания hardcoded RU | Средняя | formatter.py | EN, AR |
| 2 | AI Food промпт на русском | Средняя | ai_food.py | EN, AR |
| 3 | Ошибки только на английском | Низкая | message.py, callbacks.py | RU, AR |
| 4 | "Считаю..." на всех языках сразу | Низкая | message.py | Все |
| 5 | Единый payment URL (Tribute) | Средняя | callbacks.py | EN, AR |
| 6 | /start не определяет язык | Низкая | start.py | Все |

---

## 8. Тестовая инфраструктура

### Используемые технологии

- **pytest** + **pytest-asyncio** — async тестирование
- **unittest.mock** — AsyncMock для Telegram Bot API, DB queries
- **pytest.mark.parametrize** — параметризация по языкам
- **Реальная PostgreSQL** — integration тесты через asyncpg на Railway

### Моки vs реальная БД

| Компонент | Unit-тесты | Integration-тесты |
|-----------|-----------|-------------------|
| AI Agent (OpenRouter) | AsyncMock | Не тестируется |
| Database queries | AsyncMock | Реальная PostgreSQL |
| Telegram Bot API | AsyncMock | Не тестируется |
| Media (Google Drive) | AsyncMock | Не тестируется |
| Calculator | Реальный вызов | — |
| Formatter | Реальный вызов | — |
| i18n strings | Реальные модули | — |

### Как запустить тесты

```bash
# Все тесты (кроме DB integration)
cd bot && source .venv/bin/activate
python -m pytest tests/ -v --ignore=tests/test_db_integration.py --ignore=tests/test_e2e_integration.py

# Только DB integration (требует доступ к Railway PostgreSQL)
python -m pytest tests/test_db_integration.py -v

# Только новые тесты
python -m pytest tests/test_kbju_pipeline.py tests/test_funnel_simulation.py tests/test_callbacks_multilang.py -v

# По конкретному языку
python -m pytest tests/test_funnel_simulation.py -k "ar" -v
```

### Полный вывод тестирования

```
197 passed in 151.37s (0:02:31)

Breakdown:
  test_kbju_pipeline.py ............... 15 passed
  test_funnel_simulation.py ........... 71 passed
  test_callbacks_multilang.py ......... 40 passed
  test_db_integration.py .............. 19 passed
  test_callbacks.py ................... 22 passed
  test_funnel.py ...................... 8 passed
  test_calculator.py .................. 9 passed
  test_i18n.py ........................ 3 passed
  test_language.py .................... 10 passed
```
