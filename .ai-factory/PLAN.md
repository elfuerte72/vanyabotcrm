# Plan: Воронка "Дряблость рук" (arms variant)

**Created:** 2026-04-06
**Source:** дряблость_рук.md (ТЗ)
**Branch:** feature/ru-funnel-zones (current)

## Settings

- **Testing:** Yes
- **Logging:** Standard (existing structlog pattern)
- **Docs:** No

## Summary

Добавить третий вариант RU-воронки — `arms` (дряблость рук).
Аналогичная структура thighs-варианту: мгновенный ответ на выбор зоны + 11 стадий (1-11).
Клиентская история: Кристина ("Я похудела — но руки всё равно висят").
Цена тренировки: 690₽.

### Stage mapping (ТЗ → код)

| ТЗ шаг | Stage | Содержание | Медиа | Кнопки |
|--------|-------|-----------|-------|--------|
| 1 (instant) | zone callback | ZONE_ARMS_RESPONSE | — | — |
| 2 | 1 | Продающее (Лена до/после) | photo: ru_arms_stage_1 | buy_now |
| 3 | 2 | История Кристины (2 фото) | media group: 2a + 2b | buy_now |
| 4 | 3 | Кружочек "Как это работает" | video_note: how_it_works | — |
| 5 | 4 | Состав тренировки | — | buy_now |
| 6 | 5 | Кружочек "Подойдёт ли мне?" | video_note: will_it_suit | — |
| 7 | 6 | Жёсткий дожим + цена 690₽ | — | buy_now |
| 8 | 7 | Мягкое напоминание | — | — |
| 9 | 8 | Образовательный факт (лимфоток) | — | — |
| 10 | 9 | Чек-ин по питанию | — | buy_now |
| 11 | 10 | Последнее + фото упражнения | photo: ru_arms_stage_10 | buy_now |
| 12 | 11 | Финал / канал | — | url: channel |

### Photos mapping

| Source (photos_ru/) | Dest (bot/media/photos/) | Stage |
|---------------------|--------------------------|-------|
| F44B2E8F-642B-439A-80AD-756C52497095.jpeg | ru_arms_stage_1.jpeg | 1 |
| Нет, я конечно верила в лучшее,.jpeg | ru_arms_stage_2a.jpeg | 2 |
| IMG_9973.jpeg | ru_arms_stage_2b.jpeg | 2 |
| IMG_9995.jpeg | ru_arms_stage_10.jpeg | 10 |

## Tasks

### Phase 1: Media & Config
- [x] 1. Копировать фото из photos_ru/ в bot/media/photos/
- [x] 2. Добавить arms-фото в config/media.yaml

### Phase 2: Core Logic
- [x] 3. Добавить строки ZONE_ARMS_RESPONSE + FUNNEL_ARMS_STAGE_1..11 в ru.py
- [x] 4. Добавить arms ветку в _get_ru_funnel_message() + написать _get_ru_arms_message() в messages.py
- [x] 5. Добавить ZONE_ARMS_RESPONSE в callbacks.py response_map

### Phase 3: Testing & Scripts
- [x] 6. Создать тестовые скрипты scripts/arms/
- [x] 7. Добавить тесты для arms-варианта (TestGetFunnelMessageRUArms)
- [x] 8. Запустить тесты

## Commit Plan

- **Commit 1** (after tasks 1-5): `feat(bot): add RU funnel arms zone variant (stages 1-11)`
- **Commit 2** (after tasks 6-8): `test(bot): add arms funnel tests and test scripts`
