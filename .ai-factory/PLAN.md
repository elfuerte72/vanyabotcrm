# Plan: Проверка подписки на канал только для RU-пользователей

**Date:** 2026-03-25
**Mode:** Fast

## Settings

- **Testing:** No
- **Logging:** Standard
- **Docs:** No

## Summary

Текущий `SubscriptionMiddleware` проверяет подписку на канал для всех пользователей, но сейчас отключён. Нужно:
1. Ограничить проверку только пользователями с `language = "ru"`
2. Пользователи с `language = "en"` или `"ar"` проходят без проверки
3. Включить middleware обратно

**Ключевая проблема:** `SubscriptionMiddleware` стоит ДО `UserDataMiddleware` → нет доступа к `data["db_user"]`. Решение — переместить ПОСЛЕ `UserDataMiddleware`.

## Tasks

### Phase 1: Реализация

- [x] **Task 1:** Модифицировать `SubscriptionMiddleware` — проверять подписку только для `language=ru`
  - File: `bot/src/middlewares/subscription.py`
  - Читать `data["db_user"]` вместо детекта языка из текста
  - Если `db_user` is None или `language != "ru"` → пропустить, вызвать handler
  - Сообщение для неподписанных — только на RU
  - DEBUG-лог при пропуске для не-RU

- [x] **Task 2:** Включить middleware в `bot.py` после `UserDataMiddleware` (blocked by Task 1)
  - File: `bot/src/bot.py`
  - Раскомментировать и переставить `SubscriptionMiddleware()` после `UserDataMiddleware()`
  - Новый порядок: logging → user_data → subscription
