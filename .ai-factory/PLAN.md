# Implementation Plan: Тотальное тестирование Telegram бота

Branch: feature/telegram-bot-migration
Created: 2026-02-19

## Settings
- Testing: yes (интеграционные + unit с реальной БД)
- Logging: verbose

## Обзор

Полное тестирование бота (порт с n8n VANYA_BOT) — проверка КБЖУ расчётов, работы с БД, callback-кнопок, воронки продаж на всех языках (ru/en/ar), полный E2E цикл. Создание документации с описанием всех сообщений и кнопок.

## Тестовые данные

- Тестовые chat_id: 99990001-99990010 и 99999999
- Реальная БД: Railway PostgreSQL
- Cleanup: DELETE после каждого теста

## Commit Plan

- **Commit 1** (после задач 1-2): "test: add DB integration and callback handler tests"
- **Commit 2** (после задач 3-5): "test: add funnel, calculator, and message handler tests"
- **Commit 3** (после задач 6-7): "test: add E2E integration test and bot documentation"

## Tasks

### Phase 1: Фундамент — БД и хендлеры

- [ ] Task 1: Интеграционные тесты БД (queries.py) — все 8 функций с реальной PostgreSQL
- [ ] Task 2: Тесты callback-хендлеров — 7 handlers × 3 languages = 21 тест с моками aiogram
<!-- 🔄 Commit checkpoint: tasks 1-2 -->

### Phase 2: Воронка, калькулятор, message flow

- [ ] Task 3: Тесты воронки — 18 тестов содержимого + интеграция sender + имитация 6 дней (зависит от Task 1)
- [ ] Task 4: Расширенные тесты КБЖУ — точные расчёты, граничные значения, все activity levels
- [ ] Task 5: Тесты message handler — guard get_food, route conversation/generate, ошибки
<!-- 🔄 Commit checkpoint: tasks 3-5 -->

### Phase 3: E2E и документация

- [ ] Task 6: E2E интеграционный тест — полный цикл: создание юзера → КБЖУ → воронка 6 дней → покупка (зависит от Tasks 1,3,4)
- [ ] Task 7: Документация бота — /docs/bot-documentation.md с полным описанием сообщений, кнопок, воронки (зависит от всех тестов)
<!-- 🔄 Commit checkpoint: tasks 6-7 -->

## Ожидаемый результат

| Файл | Тестов | Описание |
|------|--------|----------|
| test_db_integration.py | ~15 | Все DB queries с реальной PostgreSQL |
| test_callbacks.py | ~21 | Callback handlers × 3 языка |
| test_funnel_integration.py | ~25 | Воронка: содержимое + sender + 6 дней |
| test_calculator_extended.py | ~15 | Расширенный КБЖУ калькулятор |
| test_message_handler.py | ~10 | Message flow: guard, routes, errors |
| test_e2e_integration.py | ~8 | Полный жизненный цикл юзера |
| **Итого новых** | **~94** | + 52 существующих = **~146 тестов** |

## Документация

- `docs/bot-documentation.md` — полное описание бота, воронки, кнопок, КБЖУ, результатов тестирования
