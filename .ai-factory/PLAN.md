# Plan: AR Funnel Rework — перевод EN воронки на арабский (ОАЭ)

**Branch:** feature/funnel-en-rework (текущая)
**Created:** 2026-03-24
**Mode:** Fast

## Settings

- **Testing:** Yes
- **Logging:** Verbose (DEBUG)
- **Docs:** No

## Description

Полная замена старой AR воронки (6 стадий, женская аудитория, $15) на новую 11-стадийную (перевод EN воронки). Арабский диалект ОАЭ (Gulf Arabic / خليجي). Мужская аудитория, 49 AED, тема сушки с сохранением мышц. Те же фото что в EN (stage 0, 6). Callback-кнопки с вопросами для мгновенной отправки следующей стадии. Тестовые скрипты в `/scripts_ar/`.

## Tasks

### Phase 1: Локализация и данные

#### Task 1: Перевести EN funnel строки на арабский (ОАЭ) в ar.py
- **Файл:** `bot/src/i18n/ar.py`
- Удалить старые `FUNNEL_DAY_*` строки (6 стадий, женская аудитория, $15)
- Добавить `FUNNEL_STAGE_0` ... `FUNNEL_STAGE_8` + `FUNNEL_STAGE_*_BUY` + `FUNNEL_STAGE_*_QUESTION`
- Добавить `UPSELL_1`, `UPSELL_2` + кнопки (`UPSELL_1_BUY`, `UPSELL_1_DECLINE`, `UPSELL_2_BUY`, `UPSELL_2_DECLINE`)
- Обновить `BUY_MESSAGE`, `VIDEO_WORKOUT_RESPONSE`, `LEARN_WORKOUT_RESPONSE` под мужскую аудиторию и 49 AED
- Арабский: Gulf Arabic (خليجي) — основной диалект ОАЭ, мужские формы обращения (يا بطل, أخوي)
- Logging: DEBUG при загрузке строк

### Phase 2: Логика воронки

#### Task 2: Обновить messages.py — заменить AR funnel на 11-стадийную
- **Файл:** `bot/src/funnel/messages.py`
- Заменить `_get_default_funnel_message()` → `_get_ar_funnel_message()`
- 11 стадий (0-8 + upsell 9-10), структура как `_get_en_funnel_message()`
- Фото: `en_stage_0` (stage 0), `en_stage_6` (stage 6) — те же файлы
- Кнопки: `buy_now` + `ar_funnel_q_{stage}` для стадий 0-8
- Upsell 9-10: `buy_now` + `upsell_decline`
- Обновить `get_funnel_message()`: для `language=="ar"` вызывать `_get_ar_funnel_message()`
- Обновить docstrings (AR: 11 stages)
- **Blocked by:** Task 1

#### Task 3: Обновить queries.py — _MAX_STAGE и timing для AR
- **Файл:** `bot/src/db/queries.py`
- `_MAX_STAGE["ar"]` = 10 (было 5)
- Timing AR = timing EN: 5min (stage 0), 1h (1-8), 24h (upsell 9)
- Удалить старый AR timing блок (2h/23h)
- Обновить docstring функции `calculate_next_send_time()`

#### Task 4: Добавить AR callback handler для кнопок-вопросов
- **Файл:** `bot/src/handlers/callbacks.py`
- Добавить `@router.callback_query(F.data.startswith("ar_funnel_q_"))` handler
- Логика: копия `handle_en_funnel_question()` с `language="ar"`
- Обновить docstring модуля, добавив `ar_funnel_q_<stage>`
- **Blocked by:** Task 2

### Phase 3: Тестовые скрипты

#### Task 5: Создать /scripts_ar/
- **Директория:** `scripts_ar/`
- `_common.py` — по структуре `scripts_en/_common.py`, `language='ar'`
- `run.sh` — runner, аналог `scripts_en/run.sh`
- `reset.py` — сброс на stage 0, language='ar'
- `stage_0.py` ... `stage_10.py` — 11 файлов, каждый вызывает `_common.send_stage(N)`
- Docstring каждого stage файла: описание стадии на английском + кнопки + фото (если есть)

### Phase 4: Тесты

#### Task 6: Написать тесты для AR воронки
- **Файл:** `bot/tests/test_funnel_ar.py` (новый файл)
- Тест: все 11 стадий AR возвращают корректные `FunnelMessage`
- Тест: stage 0 и 6 имеют `photo_name`
- Тест: `_MAX_STAGE["ar"]` == 10
- Тест: `calculate_next_send_time()` для AR: 5min/1h/24h
- Тест: callback data формат `ar_funnel_q_{0-8}`
- Паттерн: по аналогии с `bot/tests/test_funnel.py`

## Commit Plan

| # | Tasks | Commit Message |
|---|-------|---------------|
| 1 | 1-4 | `feat(bot): rework AR funnel to 11 stages — UAE Arabic translation of EN funnel` |
| 2 | 5 | `feat(scripts): add scripts_ar/ for AR funnel testing` |
| 3 | 6 | `test(bot): add AR funnel tests` |

## Key Decisions

- **Диалект:** Gulf Arabic (خليجي) — основной разговорный диалект ОАЭ. Используем مزيج из MSA + خليجي для маркетинговых текстов (понятно всем арабоговорящим, но звучит естественно для ОАЭ)
- **Фото:** Переиспользуем EN фото (en_stage_0, en_stage_6) — нет языко-зависимого текста на фото
- **Timing:** Идентичен EN — 5min/1h/24h (заменяет старый AR 2h/23h)
- **Callback prefix:** `ar_funnel_q_` (по аналогии с `en_funnel_q_`)
- **Старая AR воронка:** Полностью заменяется, FUNNEL_DAY_* удаляются из ar.py
