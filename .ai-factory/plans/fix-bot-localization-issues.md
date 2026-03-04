# Plan: Fix Bot Localization Issues

**Branch:** `fix/bot-localization-issues`
**Created:** 2026-03-04
**Source:** `docs/issues.md` — 6 проблем локализации бота

## Settings

- **Testing:** No
- **Logging:** Standard (INFO level)
- **Docs:** No

## Summary

Бот имеет 6 проблем локализации: hardcoded русские строки в formatter, AI промпт только на русском, единый payment URL, "calculating" сообщение на всех языках, ошибки на английском, /start без определения языка. Все проблемы приводят к тому, что EN/AR пользователи получают сообщения на неправильном языке.

## Tasks

### Phase 1: Quick Fixes (независимые, 1-2 строки кода)

#### ~~Task 1: Fix "calculating" message~~ ✅
- **File:** `bot/src/handlers/message.py:149-155`
- **Issue:** #4 — sends all 3 languages instead of detected one
- **Fix:** Replace multi-language block with `await message.answer(strings.CALCULATING_MENU, parse_mode="HTML")`

#### ~~Task 2: Fix payment URL for EN/AR users~~ ✅
- **Files:** `bot/config/settings.py`, `bot/src/handlers/callbacks.py:28-33`
- **Issue:** #3 — `_get_payment_url()` always returns `tribute_link`
- **Fix:** Add `ziina_link: str = ""` to Settings; return `settings.ziina_link or settings.tribute_link` for non-RU

### Phase 2: i18n Strings + Handler Fixes

#### ~~Task 3: Add missing i18n strings~~ ✅
- **Files:** `bot/src/i18n/ru.py`, `bot/src/i18n/en.py`, `bot/src/i18n/ar.py`
- **New constants:** MEAL_PLAN_READY, DAILY_TOTAL, CALORIES_LABEL, PROTEIN_LABEL, FATS_LABEL, CARBS_LABEL, KCAL, GRAM, CALC_FAILED, DEFAULT_MEAL_NAME, MEAL_TOTAL, VOICE_ERROR, VIDEO_UNAVAILABLE, START_MESSAGE

#### ~~Task 4: Fix error messages to use localized strings~~ ✅
- **Files:** `bot/src/handlers/message.py:67-68`, `bot/src/handlers/callbacks.py:65-66`
- **Issue:** #5 — error messages hardcoded in English

#### ~~Task 5: Fix /start language detection~~ ✅
- **File:** `bot/src/handlers/start.py`
- **Issue:** #6 — sends all 3 languages; use `message.from_user.language_code`

#### ~~Task 6: Localize formatter.py meal plan headers~~ ✅
- **Files:** `bot/src/services/formatter.py`, `bot/src/handlers/message.py:185`
- **Issue:** #1 — hardcoded Russian labels in `format_meal_plan_html()`
- **Fix:** Add `language` param, use `get_strings(language)` for all labels

### Phase 3: AI Prompt Localization

#### ~~Task 7: Create localized AI Food prompts~~ ✅
- **Files:** `bot/src/services/ai_food.py`, `bot/src/handlers/message.py:158`
- **Issue:** #2 — system prompt and examples entirely in Russian
- **Fix:** Create `SYSTEM_PROMPTS` dict with ru/en/ar; add `language` param to `run_agent_food()`

## Commit Plan

### Commit 1 (after Tasks 1-3):
```
fix(bot): add missing i18n strings and fix quick localization issues

- Fix calculating message to use only detected language (#4)
- Add ziina_link setting for EN/AR payment routing (#3)
- Add 14 new i18n constants across ru/en/ar modules
```

### Commit 2 (after Tasks 4-7):
```
fix(bot): localize all bot messages for EN/AR users

- Fix hardcoded error messages to use i18n (#5)
- Fix /start to detect user language (#6)
- Localize meal plan formatter headers (#1)
- Create per-language AI Food prompts (#2)
```

## Files Changed

| File | Change |
|------|--------|
| `bot/config/settings.py` | Add `ziina_link` field |
| `bot/src/i18n/ru.py` | Add 14 new string constants |
| `bot/src/i18n/en.py` | Add 14 new string constants |
| `bot/src/i18n/ar.py` | Add 14 new string constants |
| `bot/src/handlers/message.py` | Fix calculating msg, voice error, pass language to formatter & ai_food |
| `bot/src/handlers/callbacks.py` | Fix payment URL, fix video error msg |
| `bot/src/handlers/start.py` | Add language detection, use i18n |
| `bot/src/services/formatter.py` | Add language param, use i18n strings |
| `bot/src/services/ai_food.py` | Add per-language prompts, language param |
