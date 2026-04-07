# Plan: RU Funnel Glutes Zone (Форма ягодиц)

**Source:** `форма_ягодиц.md`
**Branch:** `feature/ru-funnel-zones` (current)
**Created:** 2026-04-06

## Settings

- **Testing:** Yes
- **Logging:** Standard (existing structlog pattern)
- **Docs:** Update CLAUDE.md

## Summary

Добавить ветку "Форма ягодиц" (glutes) в RU воронку — последняя из 4 зон. 11 стейджей (1-11), 9 дней. Паттерн аналогичен arms/thighs, но с ключевым отличием: **нет кружочка "Подойдёт ли мне?" на День 3** — вместо него сразу жёсткий дожим.

## Stage Mapping (ТЗ -> код)

| ТЗ Шаг | Код | Время | Содержание | Медиа |
|--------|-----|-------|------------|-------|
| 1 | ZONE_GLUTES_RESPONSE (callback) | Мгновенно | Персональная реакция | — |
| 2 | FUNNEL_GLUTES_STAGE_1 | День 0 +1ч | Фото до/после Оля + продажа | IMG_9968.jpeg |
| 3 | FUNNEL_GLUTES_STAGE_2 | День 1 10:00 | История Маши + 2 фото | "Иван, они реально.jpeg" + IMG_9998.jpeg |
| 4 | FUNNEL_GLUTES_STAGE_3 | День 1 19:00 | Кружочек "Как это работает" | video_note: how_it_works |
| 5 | FUNNEL_GLUTES_STAGE_4 | День 2 10:00 | Состав тренировки | — |
| 6 | FUNNEL_GLUTES_STAGE_5 | День 3 10:00 | Жёсткий дожим + 690р | — |
| 7 | FUNNEL_GLUTES_STAGE_6 | День 4 10:00 | Мягкое напоминание | — |
| 8 | FUNNEL_GLUTES_STAGE_7 | День 5 10:00 | Образовательный факт (два пучка) | — |
| 9 | FUNNEL_GLUTES_STAGE_8 | День 6 10:00 | Отзывы | "иван добрый день..jpeg" |
| 10 | FUNNEL_GLUTES_STAGE_9 | День 7 10:00 | Чек-ин по питанию | — |
| 11 | FUNNEL_GLUTES_STAGE_10 | День 8 10:00 | Последнее сообщение (тест приседания) | — |
| 12 | FUNNEL_GLUTES_STAGE_11 | День 9 10:00 | Финал / канал | — |

## Critical: Timing Difference

Thighs/arms: stage 5 (Day 3 10:00, video "will_it_suit") -> stage 6 (Day 3 19:00, hard sell)
Glutes: stage 5 (Day 3 10:00, hard sell) -> stage 6 (Day 4 10:00, soft reminder)

`calculate_next_send_time()` needs `variant` param. For glutes, `current_stage == 5` -> tomorrow 10:00 MSK (not same day 19:00).

## Photos Mapping

| Source (photos_ru/) | Dest (bot/media/photos/) | Stage |
|---------------------|--------------------------|-------|
| IMG_9968.jpeg | ru_glutes_stage_1.jpeg | 1 |
| Иван, они реально.jpeg | ru_glutes_stage_2a.jpeg | 2 |
| IMG_9998.jpeg | ru_glutes_stage_2b.jpeg | 2 |
| иван добрый день..jpeg | ru_glutes_stage_8.jpeg | 8 |

## Tasks

### Phase 1: Core Content
- [x] 1. i18n strings — `bot/src/i18n/ru.py`: ZONE_GLUTES_RESPONSE + FUNNEL_GLUTES_STAGE_1..11
- [x] 2. funnel messages — `bot/src/funnel/messages.py`: `_get_ru_glutes_message()` + dispatcher branch
- [x] 3. callback handler — `bot/src/handlers/callbacks.py`: add glutes to response_map

### Phase 2: Timing + Media
- [x] 4. timing fix — `bot/src/db/queries.py`: add `variant` param to `calculate_next_send_time()`, update callers
- [x] 5. media config — `config/media.yaml` + copy photos from `photos_ru/` to `bot/media/photos/`

### Phase 3: Tests + Scripts
- [x] 6. tests — `bot/tests/test_funnel.py`: TestRuGlutesFunnel class
- [x] 7. test scripts — `scripts/glutes/`: stage_0..11.py + reset.py + _common.py

### Phase 4: Docs
- [x] 8. CLAUDE.md — update funnel docs, add glutes zone info

## Commit Plan

- **Commit 1** (after tasks 1-5): `feat(bot): add RU funnel glutes zone variant (stages 1-11)`
- **Commit 2** (after tasks 6-7): `test(bot): add glutes funnel tests and test scripts`
- **Commit 3** (after task 8): `docs: update CLAUDE.md with glutes zone info`

## Button Mapping

| Stage | Кнопка | callback_data |
|-------|--------|---------------|
| 1 | FUNNEL_BUY_BUTTON | buy_now |
| 2 | FUNNEL_GET_ACCESS_BUTTON | buy_now |
| 4 | FUNNEL_TAKE_WORKOUT_BUTTON | buy_now |
| 5 | FUNNEL_HARD_SELL_BUTTON | buy_now |
| 8 | FUNNEL_READY_BUTTON | buy_now |
| 9 | FUNNEL_CHECKOUT_BUTTON | buy_now |
| 10 | FUNNEL_GLUTES_WANT_BUTTON "хочу ягодицы" | buy_now |
| 11 | FUNNEL_CHANNEL_BUTTON | URL: t.me/ivanfit_health |
