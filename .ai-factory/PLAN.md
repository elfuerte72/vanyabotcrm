# Plan: Жёсткая привязка языка при старте бота

**Mode:** Fast
**Created:** 2026-03-19
**Branch:** feature/agent-improvements (current)

## Description

Для новых пользователей (не в БД) по /start показывать выбор языка тремя inline-кнопками (English, Arabic, Russian) вместо автоопределения. Выбранный язык сохраняется в БД и используется во всех дальнейших взаимодействиях. Команда /language позволяет сменить язык в любой момент.

## Settings

- **Testing:** Yes
- **Logging:** Verbose (DEBUG + INFO)
- **Docs:** No

## Tasks

### Phase 1: Database Layer

- [x] Task 1: Добавить DB-запрос save_user_language
  - File: `bot/src/db/queries.py`
  - `save_user_language(chat_id, language, username, first_name)` — UPSERT минимальной записи
  - `update_user_language(chat_id, language)` — обновление языка существующего пользователя
  - Logging: INFO при сохранении

### Phase 2: Handlers

- [x] Task 2: Переделать /start — выбор языка для новых пользователей (blocked by: Task 1)
  - File: `bot/src/handlers/start.py`
  - Новый пользователь (db_user is None) → сообщение "Choose your language" + 3 inline-кнопки
  - Существующий пользователь → START_MESSAGE на его языке (как сейчас)
  - Вынести `_make_language_keyboard()` в отдельную функцию
  - Константа `LANGUAGE_CHOOSE_MESSAGE` в start.py (мультиязычная, не в i18n)

- [x] Task 3: Callback-хендлеры выбора языка (blocked by: Tasks 1, 2)
  - File: `bot/src/handlers/start.py`
  - `F.data.startswith("lang_")` → извлечь язык, сохранить в БД, отправить START_MESSAGE
  - Удалить кнопки из предыдущего сообщения (edit_reply_markup)

- [x] Task 4: Команда /language для смены языка (blocked by: Tasks 1, 2)
  - File: `bot/src/handlers/start.py`
  - `/language` → показать те же 3 кнопки
  - Переиспользовать `_make_language_keyboard()`

- [x] Task 5: Использовать сохранённый язык в message.py (blocked by: Task 1)
  - File: `bot/src/handlers/message.py`
  - `db_user.language` если есть, иначе fallback на `detect_language(text)`
  - Одна строка замены на ~134

### Phase 3: Tests

- [x] Task 6: Написать тесты (blocked by: Tasks 2-5)
  - File: `bot/tests/test_language_selection.py`
  - test_start_new_user_shows_language_buttons
  - test_start_existing_user_shows_message
  - test_language_callback_saves_language
  - test_language_command_shows_buttons
  - test_detected_lang_uses_db_language

## Commit Plan

**Commit 1** (после Tasks 1-5):
```
feat(bot): add language selection at /start and /language command
```

**Commit 2** (после Task 6):
```
test(bot): add language selection tests
```

## Architecture Notes

- Не используем FSM — достаточно одного UPSERT при выборе языка
- Клавиатура выбора языка — мультиязычная константа в start.py (не в i18n)
- `detect_language()` остаётся как fallback для пользователей без записи в БД
- Схема БД не меняется — поле `language` в `users_nutrition` уже есть
