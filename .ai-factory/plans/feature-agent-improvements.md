# Plan: Agent Improvements

**Branch:** `feature/agent-improvements`
**Created:** 2026-03-19
**Base:** `refactor/modular-monolith`

## Settings

- **Testing:** Yes
- **Logging:** Verbose (DEBUG)
- **Docs:** No

## Summary

Улучшение AI-агента бота без добавления фреймворков (LangChain/LangGraph не нужны):
1. Убрать эмодзи из ответов бота, задавать все вопросы одним списком
2. Добавить Pydantic-валидацию собранных данных вместо data.get() с дефолтами
3. Параллельные вызовы (asyncio.gather) для ускорения ответов
4. Retry + настраиваемая temperature для AI вызовов
5. Обрезка истории по символам для защиты от переполнения контекста
6. Тесты для всех изменений

## Tasks

### Phase 1: Prompt & Data Quality

#### Task 1: ~~Обновить SYSTEM_PROMPT — убрать эмодзи, все вопросы в одном сообщении~~ [x]
- **Files:** `bot/src/services/ai_agent.py`
- **What:**
  - Убрать все эмодзи из SYSTEM_PROMPT
  - Добавить правило "НИКОГДА не используй эмодзи"
  - Изменить стратегию: все 7 вопросов одним списком в первом сообщении
  - Обновить примеры
- **Logging:** DEBUG — длина промпта при формировании

#### Task 2: ~~Добавить Pydantic-валидацию собранных данных~~ [x]
- **Files:** `bot/src/models/user_data.py` (new), `bot/src/handlers/message.py`
- **Blocked by:** Task 1
- **What:**
  - Создать CollectedUserData (Pydantic BaseModel) с валидацией диапазонов
  - Заменить data.get() с молчаливыми дефолтами на model_validate()
  - Обработка ValidationError с логом и сообщением пользователю
- **Logging:** WARNING при validation error

### Phase 2: Performance

#### Task 3: ~~Параллельные вызовы в _process_text_message~~ [x]
- **Files:** `bot/src/handlers/message.py`, `bot/src/services/ai_agent.py`
- **Blocked by:** Task 1
- **What:**
  - В run_agent_main: asyncio.gather(get_chat_history, save_chat_message)
  - В _process_text_message: asyncio.gather(save_user_data, message.answer) при generate
  - Typing indicator перед AI вызовом
- **Logging:** DEBUG — тайминги каждого этапа

#### Task 4: ~~Retry и temperature в AI вызовы~~ [x]
- **Files:** `bot/src/services/ai_agent.py`, `bot/src/services/ai_food.py`, `bot/config/settings.py`
- **What:**
  - Добавить настройки temperature и max_retries в Settings
  - Retry в run_agent_main (аналог ai_food.py)
  - Передавать temperature в оба агента
- **Logging:** WARNING при retry

#### Task 5: ~~Обрезка истории по символам~~ [x]
- **Files:** `bot/src/services/ai_agent.py`
- **Blocked by:** Task 4
- **What:**
  - MAX_HISTORY_CHARS = 8000
  - Обрезать старые сообщения, сохраняя минимум 2 последних
- **Logging:** DEBUG — кол-во сообщений до/после, суммарная длина

### Phase 3: Tests

#### Task 6: ~~Написать тесты~~ [x]
- **Files:** `bot/tests/test_ai_agent.py` (new), `bot/tests/test_user_data_validation.py` (new)
- **Blocked by:** Tasks 1-5
- **What:**
  - Тесты обрезки истории, retry, формирования messages
  - Тесты валидации CollectedUserData
  - Обновить test_message_handler.py при необходимости

## Commit Plan

### Commit 1 (after Tasks 1-2):
```
feat(bot): rewrite agent prompt — no emojis, all questions upfront, Pydantic validation
```

### Commit 2 (after Tasks 3-5):
```
perf(bot): parallel async calls, retry logic, history trimming
```

### Commit 3 (after Task 6):
```
test(bot): add tests for agent improvements
```
