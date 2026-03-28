# Plan: CRM Chat & Events — переписка и воронка продаж

**Branch:** `feature/crm-chat-events`
**Date:** 2026-03-28
**Mode:** Full

## Settings

- **Testing:** Yes
- **Logging:** Verbose (DEBUG)
- **Docs:** No

## Summary

Бот записывает переписку в `chat_histories`, но **не сохраняет события** (нажатия кнопок воронки) в `user_events`. CRM уже имеет UI для отображения переписки и событий (`ChatHistory.tsx`), но events-лента пустая.

**Цель:** Добавить запись событий в боте → убедиться что CRM корректно отображает полную картину взаимодействия пользователя (переписка + кнопки воронки).

## Current State

### Что уже работает:
- `chat_histories` таблица заполняется ботом (human/ai сообщения)
- CRM API: `/api/chat/:sessionId` и `/api/events/:chatId` — эндпоинты есть
- `ChatHistory.tsx` мержит messages + events в единый timeline
- `shared/constants.ts` содержит `eventButtonLabels` с маппингом событий

### Что не работает:
- Бот НЕ пишет в `user_events` при нажатии кнопок воронки
- Бот НЕ пишет в `user_events` при отправке сообщений воронки
- CRM events-лента пустая для всех пользователей

## Tasks

### Phase 1: Bot — запись событий в БД

#### ~~Task 1: Добавить `save_user_event()` в bot и вызывать при нажатии кнопок~~ ✅
- **Files:** `bot/src/db/queries.py`, `bot/src/handlers/callbacks.py`
- **What:**
  - Создать `save_user_event(chat_id, event_type, event_data, language, workflow_name)` в queries.py
  - INSERT INTO user_events (chat_id, event_type, event_data, language, workflow_name)
  - Вызывать из каждого callback handler: `handle_buy_now`, `handle_en_funnel_question`, `handle_ar_funnel_question`, `handle_video_workout`, `handle_confirm_paid_ru`, `handle_upsell_decline`, и др.
  - `event_type` = "button_click", `event_data` = callback_data value
- **Logging:** DEBUG log при каждом сохранении события с chat_id, event_type, event_data

#### ~~Task 2: Добавить запись событий отправки воронки (blocked by Task 1)~~ ✅
- **Files:** `bot/src/funnel/sender.py`
- **What:**
  - При отправке каждого сообщения воронки записывать событие
  - `event_type` = "funnel_message", `event_data` = f"stage_{stage}"
  - Включить language и workflow_name
- **Logging:** DEBUG log при записи funnel_message event

### Phase 2: CRM — проверка и обновление

#### ~~Task 3: Проверить и обновить CRM events endpoint и типы (blocked by Tasks 1, 2)~~ ✅
- **Files:** `crm/server/modules/events/routes.ts`, `crm/shared/constants.ts`, `crm/shared/types.ts`
- **What:**
  - Убедиться что events endpoint возвращает все поля (включая language, workflow_name)
  - Добавить в `eventButtonLabels` новые event_data значения (en/ar funnel questions)
  - Добавить label для `funnel_message` событий
  - Проверить UserEvent type — все поля совпадают с БД

#### ~~Task 4: Проверить ChatHistory компонент (blocked by Task 3)~~ ✅
- **Files:** `crm/client/components/ChatHistory.tsx`
- **What:**
  - Проверить корректный merge messages + events по timestamp
  - Убедиться что `funnel_message` события отображаются с иконкой Mail
  - Убедиться что `button_click` события показывают правильный label из constants
  - Проверить что EN/AR события тоже отображаются корректно

### Phase 3: Тесты

#### ~~Task 5: Написать тесты (blocked by Tasks 1-4)~~ ✅
- **Files:** `bot/tests/test_user_events.py`, `crm/server/__tests__/events.test.ts`
- **What:**
  - Bot: тест `save_user_event()` — проверить INSERT query и параметры
  - Bot: тест callback handler — мокнуть save_user_event, проверить вызов
  - CRM: тест events endpoint — мокнуть pool.query, проверить response format

## Commit Plan

1. **После Phase 1 (Tasks 1-2):**
   `feat(bot): save funnel button clicks and messages to user_events table`

2. **После Phase 2 (Tasks 3-4):**
   `feat(crm): update events display for new bot event types`

3. **После Phase 3 (Task 5):**
   `test: add tests for user events tracking (bot + crm)`
