# Plan: Comprehensive Bot Testing (RU/EN/AR)

**Branch:** `test/comprehensive-bot-testing`
**Created:** 2026-03-04
**Description:** Комплексное тестирование Telegram бота: КБЖУ pipeline, воронка продаж (симуляция 6 дней), callback-обработчики, обновление CRM данных. Все тесты × 3 языка (RU/EN/AR) с итоговым summary поведения бота.

## Settings

| Setting | Value |
|---------|-------|
| Testing | Yes |
| Logging | Verbose (DEBUG) |
| Docs | No |
| DB Mode | Mocks + Real DB (integration) |

---

## Phase 1: Test Infrastructure

### Task 1: Тестовые fixtures для 3 языков [DONE]
- **Файлы:** `bot/tests/conftest.py` (расширить), `bot/tests/helpers.py` (новый)
- **Содержание:**
  - Фабрики пользователей: `make_user(lang="ru")` → User dataclass с реалистичными данными
  - Профили для КБЖУ: мужчина RU, женщина EN, мужчина AR
  - Мок-хелперы: `_make_bot()`, `_make_callback(data, user_id, lang)`, `_make_message(text, chat_id)`
  - JSON-ответы AI агента: `agent_response_ru/en/ar` с `is_finished=True`
  - Примеры meal plan JSON для всех 3 языков
- **Логирование:** DEBUG для fixture создания

---

## Phase 2: КБЖУ Pipeline Tests

### Task 2: КБЖУ pipeline (мок-тесты) [DONE]
- **Файл:** `bot/tests/test_kbju_pipeline.py`
- **Зависит от:** Task 1
- **Тест-кейсы:**
  1. `test_kbju_pipeline_ru` — русский пользователь, полный pipeline
  2. `test_kbju_pipeline_en` — английский пользователь
  3. `test_kbju_pipeline_ar` — арабский пользователь
  4. `test_calculate_macros_saved_to_db` — проверить что save_user_data получает правильные КБЖУ
  5. `test_set_food_received_starts_funnel` — после отправки меню funnel_stage=0
  6. `test_language_detected_and_saved` — detect_language → сохранение в БД
  7. `test_already_calculated_blocks_repeat` — get_food=TRUE → блокировка
- **Моки:** `run_agent_main`, `run_agent_food`, `save_user_data`, `set_food_received`, `get_user`
- **Assertions:** Проверить вызовы DB-функций с правильными аргументами

### Task 3: Integration тесты с реальной БД [DONE]
- **Файл:** `bot/tests/test_db_integration.py` (расширить)
- **Тест-кейсы:**
  1. `test_save_user_data_full_upsert` — все поля записываются
  2. `test_save_user_data_updates_on_conflict` — повторный вызов обновляет
  3. `test_set_food_received_sets_funnel` — funnel_stage=0, get_food=TRUE
  4. `test_mark_as_buyer_sets_flag` — is_buyer=TRUE
  5. `test_advance_funnel_conditional` — только если текущий stage совпадает
  6. `test_get_funnel_targets_excludes_buyers` — buyer не попадает
  7. `test_get_funnel_targets_stage_range` — только stage 0-4
- **Cleanup:** DELETE WHERE chat_id IN (99990001-99990010)

---

## Phase 3: Funnel Simulation

### Task 4: Симуляция воронки × 3 языка [DONE]
- **Файл:** `bot/tests/test_funnel_simulation.py`
- **Зависит от:** Task 1
- **Тест-кейсы:**
  1. `test_full_funnel_cycle_ru` — 6 дней полный цикл на русском
  2. `test_full_funnel_cycle_en` — на английском
  3. `test_full_funnel_cycle_ar` — на арабском
  4. `test_funnel_stage_increment` — stage 0→1→2→3→4→5
  5. `test_buyer_excluded_from_funnel` — покупатель не получает сообщения
  6. `test_funnel_error_resilience` — ошибка одного пользователя не блокирует
  7. `test_funnel_message_text_matches_i18n` — текст совпадает с i18n строками
  8. `test_funnel_buttons_correct_per_stage` — правильные кнопки на каждом stage
  9. `test_funnel_mixed_languages` — несколько пользователей с разными языками
- **Моки:** `bot.send_message` (AsyncMock), `get_funnel_targets`, `update_funnel_stage`
- **Ключевые проверки:**
  - Текст = `get_strings(lang).FUNNEL_DAY_N`
  - Кнопки = `get_strings(lang).FUNNEL_DAY_N_BUTTONS`
  - Stage increment: `update_funnel_stage` вызван после отправки

---

## Phase 4: Callback Tests

### Task 5: Callbacks × 3 языка [DONE]
- **Файл:** `bot/tests/test_callbacks_multilang.py`
- **Зависит от:** Task 1
- **7 callback × 3 языка = 21 тест-кейс + edge cases:**

| Callback | Проверки |
|----------|----------|
| `buy_now` | mark_as_buyer вызван, BUY_MESSAGE на языке, URL кнопка |
| `show_info` | send_info_video вызван |
| `show_results` | send_random_result_photo, RESULTS_CAPTION на языке |
| `check_suitability` | send_suitability_video вызван |
| `remind_later` | REMIND_LATER текст на языке |
| `none` | NONE_RESPONSE текст на языке |
| `video_workout` | VIDEO_WORKOUT_RESPONSE, advance_funnel_if_at_stage(1) |

- **Доп. тест-кейсы:**
  - CRM обновление: mark_as_buyer → is_buyer=TRUE в данных CRM
  - advance_funnel: video_workout → funnel_stage условно +1
  - Кнопки: правильная InlineKeyboard конфигурация
- **Моки:** `get_user_language`, `mark_as_buyer`, media-сервисы, bot API

---

## Phase 5: Summary Documentation

### Task 6: Summary поведения бота [DONE]
- **Файл:** `bot/tests/BOT_BEHAVIOR_SUMMARY.md`
- **Зависит от:** Tasks 2, 4, 5
- **Содержание:**
  - Таблица текстов бота по языкам
  - Воронка: текст + кнопки для каждого дня
  - Callback ответы на каждом языке
  - Различия: цены, тон, пробелы в локализации

---

## Commit Plan

| Checkpoint | Tasks | Message |
|------------|-------|---------|
| Commit 1 | 1 | `test: add multilingual test fixtures and helpers` |
| Commit 2 | 2, 3 | `test: add KBJU pipeline and DB integration tests` |
| Commit 3 | 4, 5 | `test: add funnel simulation and callback tests (RU/EN/AR)` |
| Commit 4 | 6 | `docs: add bot behavior summary per language` |
