# Plan: Полная переработка воронки сообщений (RU)

**Branch:** `feature/funnel-ru-rework`
**Created:** 2026-03-21
**Source:** `days.md`

## Settings

- **Testing:** Yes
- **Logging:** Verbose (DEBUG)
- **Docs:** No

## Overview

Полная переработка воронки продающих сообщений после расчёта КБЖУ для русскоязычных пользователей (language = "ru"). Текущая воронка (6 стадий, 990₽) заменяется на новую (8 стадий, 690₽) с:
- Фото до/после (локальные файлы)
- Видеокружочками (Google Drive)
- Индивидуальными таймингами (конкретное время дня МСК)
- Более мягким подходом (финал — подписка на канал, не продажа)

## Маппинг стадий

| Stage | Логический день | Время | Задержка | Контент |
|-------|----------------|-------|----------|---------|
| 0 | День 0 | +30 мин | 30 мин после КБЖУ | Подарок: утренняя активация 7 мин |
| 1 | День 0 | +3ч | 2.5ч после stage 0 | Фото до/после + тизер тренировки |
| 2 | День 1 | 10:00 MSK | след. день | История Маши + фото до/после |
| 3 | День 2 | 10:00 MSK | след. день | Кружочек "как это работает" |
| 4 | День 2 | 19:00 MSK | +9ч | Подробное описание тренировки |
| 5 | День 3 | 19:00 MSK | след. день | Sales pitch: 690₽, кнопка покупки + кружочек |
| 6 | День 4 | 11:00 MSK | след. день | Мягкое напоминание, 690₽ |
| 7 | День 5 | 10:00 MSK | след. день | Благодарность + канал (без продажи) |

## Ключевые изменения

### Архитектура
- **Таймер**: `last_funnel_msg_at + interval` → `next_funnel_msg_at` (точные абсолютные времена)
- **Стадии**: 0-5 → 0-7 (8 сообщений)
- **Медиа**: новый тип — локальные фото + видеокружочки
- **FunnelMessage**: расширение dataclass для фото и кружочков

### Контент (только RU)
- Цена: 990₽ → 690₽ (скидка с 1390₽ вместо 1900₽)
- Стиль: менее агрессивный, более личный
- Финал: подписка на канал вместо продажи
- Личная поддержка: ссылка @Ivan_Razmazin
- EN/AR воронка НЕ затрагивается

### Callbacks
- Новый: `learn_workout` (узнать про тренировку)
- Новый: `video_circle` (отправка кружочка)
- Обновлён: `video_workout` (убран delayed followup)
- Сохранены: `buy_now`, `remind_later`, `none` (для EN/AR)

## Tasks

### Phase 1: Инфраструктура (можно параллельно)

**Task 1: Миграция БД — next_funnel_msg_at** ✅
- Добавить колонку `next_funnel_msg_at TIMESTAMPTZ` в `users_nutrition`
- Функция `calculate_next_send_time(current_stage) -> datetime`
- Обновить SQL: `set_food_received()`, `get_funnel_targets()`, `update_funnel_stage()`
- Файлы: `src/db/queries.py`, `db/schema.sql`

**Task 2: Локальные фото — инфраструктура** ✅ (blocked by: Task 1)
- Папка `bot/media/photos/`, копирование фото
- `send_local_photo()` и `send_funnel_photo()` в `src/services/media.py`
- Файлы: `src/services/media.py`, `config/media.yaml`

**Task 3: Тексты воронки в ru.py** ✅ (независимая)
- 8 новых FUNNEL_STAGE_0..7 из days.md
- Обновить callback responses
- Файлы: `src/i18n/ru.py`

**Task 7: media.yaml — новые видео** ✅ (независимая)
- Video notes file IDs, funnel photos paths
- Файлы: `config/media.yaml`

### Phase 2: Логика (зависит от Phase 1)

**Task 4: FunnelMessage + get_funnel_message()** ✅ (blocked by: Task 2, 3)
- Расширить dataclass (photo_name, video_note)
- 8 стадий в get_funnel_message()
- Файлы: `src/funnel/messages.py`

**Task 5: sender.py — новые типы сообщений** ✅ (blocked by: Task 1, 4)
- Отправка фото с caption, видеокружочков
- Использование calculate_next_send_time()
- Файлы: `src/funnel/sender.py`

**Task 6: Callback handlers** ✅ (blocked by: Task 3, 4)
- Новые: learn_workout, video_circle
- Обновить buy_now, video_workout
- Файлы: `src/handlers/callbacks.py`

### Phase 3: Тесты

**Task 8: Unit-тесты** ✅ (blocked by: все остальные)
- test_funnel_messages.py, test_funnel_timing.py
- Файлы: `tests/`

## Commit Plan

**Commit 1** (после Tasks 1, 2, 3, 7):
```
feat(funnel): add next_funnel_msg_at, local photos, new RU funnel texts
```

**Commit 2** (после Tasks 4, 5, 6):
```
feat(funnel): rework message types, sender, and callbacks for 8-stage RU funnel
```

**Commit 3** (после Task 8):
```
test(funnel): add tests for new funnel stages, timing, and content
```
