# Plan: Оптимизация скорости ответа бота

**Mode:** Fast
**Created:** 2026-03-22
**Source:** `.ai-factory/plans/performance-optimization.md`

## Settings

- **Testing:** Yes
- **Logging:** Verbose (DEBUG)
- **Docs:** No

## Summary

4 оптимизации для ускорения ответа бота на inline-кнопки:
1. Увеличение пула соединений (min_size 2→5)
2. Устранение дублирующих DB-запросов в callback-хендлерах
3. In-memory кеш Telegram file_id для медиа-файлов
4. Partial index для запроса funnel targets

## Tasks

### Phase 1: Quick Wins (1 коммит)

#### ~~Task 1: Увеличить min_size пула соединений до 5~~ [x]
- **File:** `bot/src/db/pool.py:36`
- **Change:** `min_size=2` → `min_size=5`
- **Logging:** DEBUG лог при создании пула с min_size/max_size
- **Risk:** Низкий — одна строка

#### ~~Task 2: Убрать дублирующие DB-запросы в callbacks.py~~ [x]
- **File:** `bot/src/handlers/callbacks.py`
- **Change:** В 8 хендлерах заменить `await get_user_language(user_id)` на `data["db_user"].language` (уже загружен UserDataMiddleware)
- **Pattern:**
  ```python
  # Было:
  language = await get_user_language(user_id) or "en"
  # Стало:
  db_user = data.get("db_user")
  language = db_user.language if db_user else "en"
  ```
- **Handlers:** handle_buy_now, handle_show_info, handle_show_results, handle_remind_later, handle_none, handle_video_workout, handle_learn_workout, handle_video_circle
- **Logging:** DEBUG лог при получении языка из db_user
- **Depends on:** UserDataMiddleware уже работает (`src/middlewares/user_data.py`)

### Phase 2: File ID Cache (1 коммит)

#### ~~Task 3: Реализовать file_id кеш в media.py~~ [x]
- **File:** `bot/src/services/media.py`
- **Change:** Добавить `_tg_file_id_cache: dict[str, str] = {}`. Все 5 send-функций: проверять кеш перед скачиванием, сохранять file_id после первой отправки.
- **Functions:** send_info_video, send_suitability_video, send_random_result_photo, send_video_note_from_drive, send_local_photo
- **File ID extraction:** `message.video.file_id`, `message.photo[-1].file_id`, `message.video_note.file_id`
- **Logging:** DEBUG лог cache hit/miss с ключом
- **Effect:** -90% время отправки медиа после прогрева

### Phase 3: Database Index (1 коммит)

#### ~~Task 4: Создать миграцию с составным индексом~~ [x]
- **File:** `db/migrations/003_add_funnel_targets_index.sql`
- **SQL:**
  ```sql
  CREATE INDEX IF NOT EXISTS idx_funnel_targets
  ON users_nutrition (next_funnel_msg_at)
  WHERE get_food = TRUE
    AND (is_buyer IS FALSE OR is_buyer IS NULL)
    AND funnel_stage >= 0;
  ```
- **Also:** Обновить `db/schema.sql`

### Phase 4: Tests (1 коммит)

#### ~~Task 5: Обновить тесты callbacks (blocked by: Task 2)~~ [x]
- **File:** `bot/tests/test_callbacks.py`, `bot/tests/test_callbacks_multilang.py`
- **Change:** Убрать mock `get_user_language`, передавать `db_user` через data dict
- **Verify:** db_user=None → fallback "en"

#### ~~Task 6: Добавить тесты для file_id кеша (blocked by: Task 3)~~ [x]
- **File:** `bot/tests/test_media.py` (новый)
- **Tests:** cache miss → download, cache hit → no download, local photo cache, reset between tests

## Commit Plan

| # | Tasks | Commit Message |
|---|-------|---------------|
| 1 | 1, 2 | `perf(bot): increase pool min_size, eliminate duplicate DB queries in callbacks` |
| 2 | 3 | `perf(bot): add in-memory Telegram file_id cache for media` |
| 3 | 4 | `perf(db): add partial index for funnel targets query` |
| 4 | 5, 6 | `test(bot): update callback tests, add media cache tests` |

## Expected Impact

| Optimization | Before | After |
|---|---|---|
| Callback media response | 1.5-2.5 sec | ~0.1 sec (after warmup) |
| DB queries per callback | 2 | 1 |
| Pool cold connections | 8 on-demand | 5 always warm |
| Funnel query | seq scan | index scan |
