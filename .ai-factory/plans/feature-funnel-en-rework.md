# Plan: EN Funnel Rework (9 stages + 2 upsells)

- **Branch:** `feature/funnel-en-rework`
- **Created:** 2026-03-23
- **Base branch:** `feature/funnel-ru-rework`

## Settings

- **Testing:** Yes — update existing tests + add new for question-button callbacks
- **Logging:** Verbose (DEBUG level)
- **Docs:** No

## Description

Переделать EN воронку по аналогии с RU: 9 основных стадий (0-8) + 2 upsell (9-10), с фото, кнопками-вопросами и новым таймингом. Целевая аудитория — мужчины (workout для удержания мышц при дефиците). Ценник: 49 AED.

### Key Changes from Current EN Funnel

| Aspect | Current | New |
|--------|---------|-----|
| Stages | 6 (0-5) | 9 + 2 upsell (0-10) |
| Audience | Women | Men |
| Photos | None | 2 photos (stages 0, 6) |
| Buttons | Generic buy/info | Buy + question (triggers next stage) |
| Timing | 2h first, 23h rest | 5 min first, 1h rest (instant on question button) |
| Product | $15 workout (women) | 49 AED workout (men, muscle retention) |
| Upsells | None | Technique check (79 AED) + 7-day coaching (129 AED) |

### Question Button Mechanism (NEW)

Each stage has 2 buttons:
- `✅ Get Access — 49 AED` → buy_now callback (payment flow)
- `❓ <question>` → **instantly sends next funnel stage** + updates funnel_stage + resets next_funnel_msg_at

If user doesn't click any button, scheduler sends next stage after 1 hour.

## Tasks

### Phase 1: Content & Media

**Task 1: Copy photos to bot/media/photos/** ✅
- Copy `photo_en/2026-03-22 21.06.11.jpg` → `bot/media/photos/en_funnel_stage_0.jpg`
- Copy `photo_en/Gemini_Generated_Image_e7174we7174we717.png` → `bot/media/photos/en_funnel_stage_6.png`
- Add entries to `config/media.yaml` under `photos.funnel` for EN stages
- Log: DEBUG when photo paths resolved

**Task 2: Update EN strings in src/i18n/en.py** ✅
- Replace all `FUNNEL_DAY_*` with `FUNNEL_STAGE_*` (9 stages 0-8)
- Add `UPSELL_1` and `UPSELL_2` message texts
- Add button labels for each stage (buy + question)
- Add callback response texts for question buttons
- All texts from `days_en.md`
- Log: N/A (static strings)

### Phase 2: Core Logic

**Task 3: Update funnel messages in src/funnel/messages.py** ✅
- Create `_get_en_funnel_message(stage, s)` with 11 stages (0-10)
- Stage 0: photo `en_funnel_stage_0.jpg`, 2 buttons
- Stage 6: photo `en_funnel_stage_6.png`, 2 buttons
- Stages 1-5, 7-8: text + 2 buttons (buy + question)
- Stages 9-10: upsell messages with buy + decline buttons
- Update `get_funnel_message()`: EN → `_get_en_funnel_message()`
- Log: DEBUG for each stage resolution with photo/button info

**Task 4: Update timing in src/db/queries.py** ✅
- `_MAX_STAGE["en"] = 10` (was 5)
- Stage 0 → +5 min (not +2h)
- Stages 1-8 → +1 hour (not +23h)
- Stage 8 (after buy) → handled by payment callback
- Stage 9 (upsell 1) → +24 hours
- Stage 10 → None (last stage)
- Log: DEBUG with calculated next_send_time

### Phase 3: Callback Handlers

**Task 5: Add question-button callback handler** ✅
- New callback pattern: `en_funnel_q_<stage>` for question buttons
- Handler: fetch user → get next stage message → send it → update funnel_stage + next_funnel_msg_at
- Reuse `_send_single_funnel_message()` from sender.py or extract shared send logic
- Handle edge cases: user already advanced past this stage, user is buyer
- Log: INFO for each instant funnel advance, DEBUG for state changes

### Phase 4: Sender Integration

**Task 6: Verify sender.py handles EN photos** ✅
- Ensure `_send_single_funnel_message()` works with `.png` files (not just `.jpg`)
- Verify caption + keyboard sent with photo
- Log: DEBUG for photo send attempts

### Phase 5: Tests

**Task 7: Update tests** ✅
- `test_funnel.py`: 11 EN stages, verify texts/buttons/photos
- `test_funnel_timing.py`: new EN timing (5min, 1h intervals, 24h upsell)
- New tests for question-button callback handler (instant stage advance)
- Test edge cases: double-click, buyer skipping, last stage

## Commit Plan

**Commit 1** (after Tasks 1-2): `feat(bot): add EN funnel content — 9 stages + 2 upsells with photos`

**Commit 2** (after Tasks 3-4): `feat(bot): rework EN funnel messages and timing — 11 stages, 1h intervals`

**Commit 3** (after Tasks 5-6): `feat(bot): add question-button instant funnel advance for EN`

**Commit 4** (after Task 7): `test(bot): update EN funnel tests for new 11-stage flow`
