# Plan: RU Funnel with Zone Branching

**Branch:** `feature/ru-funnel-zones`
**Created:** 2026-04-06
**ТЗ:** `new_ru(низ_живота).md`

## Settings

- **Testing:** Yes
- **Logging:** Verbose (DEBUG)
- **Docs:** Yes (CLAUDE.md + FUNNELS.md)

## Summary

Полная замена RU-воронки. Вместо линейных 8 этапов (0-7) — 13 этапов (0-12) с ветвлением по проблемным зонам тела. Этап 0 — общий (выбор зоны из 4 вариантов), этапы 1-12 — зоноспецифичные. В этой итерации реализуем только ветку "Низ живота" (variant=`belly`). Архитектура поддерживает все 4 варианта.

## Architecture

```
User gets meal plan → set_food_received() → funnel_stage=0, +30min
         │
    Stage 0 (common): "Какая зона беспокоит тебя больше всего?"
    4 buttons: belly / thighs / arms / glutes
         │
    ┌────┤ User clicks zone button (callback)
    │    └── No click → resend stage 0 every 24h
    │
    ▼
    Zone callback: set funnel_variant, advance to stage 1, schedule +1h
    Send instant response: "Понял тебя 🤍 Низ живота — одна из..."
         │
    Stages 1-12: zone-specific messages (scheduler)
```

### New DB Column

`funnel_variant TEXT DEFAULT NULL` on `users_nutrition`
Values: `belly` | `thighs` | `arms` | `glutes` | NULL

### New Stage Map (RU)

| Stage | Timing | Content | Media | Buttons |
|-------|--------|---------|-------|---------|
| 0 | +30min | Common: zone selection + morning activation | — | 4 zone buttons + "Разбудить тело" |
| 1 | +1h after zone | Selling: before/after photo | ru_belly_stage_1.jpeg | buy_now |
| 2 | Day 1, 10:00 | Client story (Лейла) | 2 photos (media group) | buy_now |
| 3 | Day 1, 19:00 | "Как это работает" | video_note: how_it_works | — |
| 4 | Day 2, 10:00 | Workout contents detail | — | buy_now |
| 5 | Day 3, 10:00 | "Подойдёт ли мне?" | video_note: will_it_suit | — |
| 6 | Day 3, 19:00 | Hard sell | — | buy_now |
| 7 | Day 4, 10:00 | Soft reminder | — | — |
| 8 | Day 5, 10:00 | Educational fact | — | — |
| 9 | Day 6, 10:00 | Reviews | 2 photos (media group) | buy_now |
| 10 | Day 7, 10:00 | Nutrition check-in | — | buy_now |
| 11 | Day 8, 10:00 | Last workout message | ru_belly_stage_11.png | buy_now |
| 12 | Day 9, 10:00 | Farewell + channel | — | URL: t.me/ivanfit_health |

### Timing (calculate_next_send_time)

| After stage | Next at |
|-------------|---------|
| 0 (no zone) | +24h (resend) |
| zone callback → 1 | +1h |
| 1 → 2 | tomorrow 10:00 MSK |
| 2 → 3 | same day 19:00 MSK |
| 3 → 4 | tomorrow 10:00 MSK |
| 4 → 5 | tomorrow 10:00 MSK |
| 5 → 6 | same day 19:00 MSK |
| 6 → 7 | tomorrow 10:00 MSK |
| 7 → 8 | tomorrow 10:00 MSK |
| 8 → 9 | tomorrow 10:00 MSK |
| 9 → 10 | tomorrow 10:00 MSK |
| 10 → 11 | tomorrow 10:00 MSK |
| 11 → 12 | tomorrow 10:00 MSK |

### Photos Mapping

| Source (photos_ru/) | Target (bot/media/photos/) | Stage |
|---------------------|----------------------------|-------|
| IMG_9973.jpeg | ru_belly_stage_1.jpeg | 1 |
| IMG_9970.jpeg | ru_belly_stage_2a.jpeg | 2 |
| Иван! Ура.jpeg | ru_belly_stage_2b.jpeg | 2 |
| FAB45863-...jpeg | ru_belly_stage_9a.jpeg | 9 |
| Это был для меня такой.jpeg | ru_belly_stage_9b.jpeg | 9 |
| СКРУЧИВАНИЕ.png | ru_belly_stage_11.png | 11 |

## Tasks

### Phase 1: Infrastructure (tasks 1-2)
- [x] 1. **DB миграция** — `funnel_variant` column + update User model
- [x] 2. **Фото** — copy to bot/media/photos/, update media.yaml

### Phase 2: Core (tasks 3-5)
- [x] 3. **FunnelMessage** — add `extra_photos` field + media group support in sender
- [x] 4. **RU strings** — rewrite i18n/ru.py with 13 stages + zone buttons
- [x] 5. **RU messages** — rewrite `_get_ru_funnel_message` with variant support

### Phase 3: Logic (tasks 6-7)
- [x] 6. **DB queries** — new timing, targets, zone selection, sender stage-0 logic
- [x] 7. **Callbacks** — zone selection handlers + update existing callbacks

### Phase 4: Testing (tasks 8-9)
- [x] 8. **Scripts** — test scripts for each stage (send to chat_id 379336096)
- [x] 9. **Unit tests** — messages, timing, zone selection

### Phase 5: Docs (task 10)
- [x] 10. **Documentation** — update CLAUDE.md + FUNNELS.md

## Commit Plan

- **Commit 1** (after tasks 1-2): `feat(bot): add funnel_variant column and copy zone photos`
- **Commit 2** (after tasks 3-5): `feat(bot): rewrite RU funnel messages with zone branching`
- **Commit 3** (after tasks 6-7): `feat(bot): implement zone selection logic and callbacks`
- **Commit 4** (after tasks 8-9): `feat(bot): add funnel test scripts and unit tests`
- **Commit 5** (after task 10): `docs: update CLAUDE.md and FUNNELS.md for new RU funnel`

## Key Decisions

1. **Stage 0 не инкрементируется** — scheduler отправляет stage 0 и reschedule +24h, пока юзер не выберет зону. Только zone callback двигает на stage 1.
2. **Media groups** — этапы с 2+ фото отправляются как MediaGroup (album). Caption на первом фото, кнопки отдельным сообщением.
3. **Variant в messages** — `get_funnel_message(stage, language, variant=None)`. Для RU stages 1+ variant обязателен. Для EN/AR игнорируется.
4. **Только "belly"** в этой итерации — остальные 3 варианта добавим позже по аналогии.
