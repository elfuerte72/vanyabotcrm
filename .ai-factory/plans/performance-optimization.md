# ТЗ: Оптимизация скорости ответа бота

## Проблема

При нажатии inline-кнопок (callbacks) бот отвечает медленно — от 1 до 3 секунд.
Причины: скачивание медиа с Google Drive, лишние запросы к БД, холодный пул соединений.

---

## Часть 1: Telegram file_id кеш (in-memory dict)

### Как работает сейчас (МЕДЛЕННО)

Каждая отправка видео/фото из Google Drive:
```
Пользователь нажал кнопку
  → httpx GET Google Drive (~1-2 сек, скачивание файла в RAM)
  → bot.send_video(BufferedInputFile(data)) (~0.5 сек, загрузка в Telegram)
  → Итого: 1.5-2.5 сек
```

Это происходит КАЖДЫЙ раз, даже если файл тот же самый.

### Как должно работать (БЫСТРО)

Первая отправка (прогрев):
```
  → httpx GET Google Drive (~1-2 сек)
  → bot.send_video(BufferedInputFile(data)) → Telegram возвращает Message
  → Из Message достаём file_id (строка типа "BAACAgIAAxkBAAI...")
  → Сохраняем в dict: _cache[gdrive_id] = telegram_file_id
```

Все следующие отправки:
```
  → bot.send_video(video=telegram_file_id) → мгновенно (~0.1 сек)
  → Google Drive вообще не трогаем
```

### Что менять

**Файл: `bot/src/services/media.py`**

1. Добавить модульный dict-кеш:
```
_tg_file_id_cache: dict[str, str] = {}
```

2. Изменить все функции отправки медиа (`send_info_video`, `send_suitability_video`, `send_random_result_photo`, `send_video_note_from_drive`):
   - Перед скачиванием проверить: есть ли gdrive_id в `_tg_file_id_cache`
   - Если есть — отправить по file_id (без скачивания)
   - Если нет — скачать, отправить как BufferedInputFile, из ответа Telegram достать file_id, сохранить в кеш

3. Также кешировать локальные фото (`send_local_photo`):
   - После первой отправки FSInputFile → сохранить file_id
   - Следующие отправки — по file_id

### Как достать file_id из ответа Telegram

- `bot.send_video()` возвращает `Message` → `message.video.file_id`
- `bot.send_photo()` возвращает `Message` → `message.photo[-1].file_id`
- `bot.send_video_note()` возвращает `Message` → `message.video_note.file_id`

### Какие файлы кешируются

Из `media.yaml`:

| Ключ | Тип | Используется в |
|------|-----|---------------|
| `videos.info` | video | callback `show_info` |
| `videos.suitability` | video | callback `check_suitability` |
| `video_notes.how_it_works` | video_note | funnel stage 3, callback `video_circle` |
| `video_notes.will_it_suit` | video_note | funnel stage 5 |
| `photos.results[0..2]` | photo | callback `show_results` (3 фото) |
| `photos.funnel.stage_1` | photo (локальная) | funnel stage 1 |
| `photos.funnel.stage_2` | photo (локальная) | funnel stage 2 |

Итого: 7 файлов → 7 записей в dict. Потребление памяти: ~1 КБ.

### Поведение при рестарте бота

- Dict обнуляется при перезапуске
- Первый пользователь, который вызовет каждый файл, "прогреет" кеш
- Все последующие пользователи получат мгновенный ответ

### Ожидаемый эффект

- Callback `show_info`: с ~2 сек → ~0.1 сек (после прогрева)
- Callback `show_results`: с ~1 сек → ~0.1 сек
- Funnel stage 3 (видео-кружок): с ~1.5 сек → ~0.1 сек
- Funnel stage 5 (видео-кружок): с ~1.5 сек → ~0.1 сек

---

## Часть 2: Убрать дублирующие DB-запросы

### Как работает сейчас (2 запроса)

На каждый callback выполняется:

1. **UserDataMiddleware** (`bot/src/middlewares/user_data.py:33`):
   ```
   SELECT * FROM users_nutrition WHERE chat_id = $1
   ```
   Результат → `data["db_user"]` (полный объект User, включая `language`)

2. **Внутри хендлера** (`bot/src/handlers/callbacks.py:42`):
   ```
   language = await get_user_language(user_id)
   → SELECT language FROM users_nutrition WHERE chat_id = $1
   ```

Это два запроса к одной таблице по одному `chat_id`. Второй — лишний.

### Как должно работать (1 запрос)

Хендлеры должны брать язык из уже загруженного `db_user`:

```
db_user = data["db_user"]  # уже загружен в middleware
language = db_user.language if db_user else "en"
```

### Что менять

**Файл: `bot/src/handlers/callbacks.py`**

Во всех хендлерах заменить:
```
language = await get_user_language(user_id) or "en"
```
на получение языка из `data["db_user"]`.

Для этого нужно добавить `data: dict` в параметры хендлеров (aiogram передаёт middleware data через kwargs).

**Затронутые хендлеры (8 штук):**
- `handle_buy_now` (строка 42)
- `handle_show_info` (строка 70)
- `handle_show_results` (строка 83)
- `handle_remind_later` (строка 113)
- `handle_none` (строка 127)
- `handle_video_workout` (строка 146)
- `handle_learn_workout` (строка 175)
- `handle_video_circle` (строка 215)

### Ожидаемый эффект

- Минус 1 DB-запрос на каждый callback (~5-50 мс)
- Снижение нагрузки на Supabase

---

## Часть 3: Оптимизация пула соединений

### Как работает сейчас

**Файл: `bot/src/db/pool.py:36-41`**

```
min_size=2   ← только 2 соединения "тёплые"
max_size=10
```

При всплеске (10 пользователей одновременно нажали кнопки) — 8 соединений создаются на лету.
Каждое новое соединение: SSL handshake к Supabase Supavisor = 20-50 мс.

### Что менять

**Файл: `bot/src/db/pool.py`**

- `min_size=2` → `min_size=5`
- Всё остальное без изменений

### Ожидаемый эффект

- Нет задержки на создание соединений при умеренной нагрузке
- 5 соединений всегда готовы к работе

---

## Часть 4: Составной индекс для запроса воронки

### Как работает сейчас

Запрос `get_funnel_targets()` (`bot/src/db/queries.py`) фильтрует по:
```sql
WHERE (is_buyer IS FALSE OR is_buyer IS NULL)
  AND get_food = TRUE
  AND funnel_stage >= 0
  AND (next_funnel_msg_at IS NOT NULL AND next_funnel_msg_at <= NOW())
```

Существующие индексы: отдельно на `funnel_stage`, отдельно на `is_buyer`.
Нет составного индекса — PostgreSQL не может эффективно объединить условия.

### Что менять

**Новая миграция: `db/migrations/003_add_funnel_targets_index.sql`**

```sql
CREATE INDEX IF NOT EXISTS idx_funnel_targets
ON users_nutrition (next_funnel_msg_at)
WHERE get_food = TRUE
  AND (is_buyer IS FALSE OR is_buyer IS NULL)
  AND funnel_stage >= 0;
```

Partial index — покрывает точно тот WHERE, который использует запрос.

### Ожидаемый эффект

- Запрос воронки: с полного сканирования → index scan
- Не влияет напрямую на callback-кнопки, но ускоряет cron-задачу отправки воронки

---

## Сводка изменений

| # | Что | Файлы | Эффект |
|---|-----|-------|--------|
| 1 | file_id кеш | `bot/src/services/media.py` | -90% время отправки медиа |
| 2 | Убрать дубль DB-запросов | `bot/src/handlers/callbacks.py` | -1 запрос на callback |
| 3 | Пул min_size=5 | `bot/src/db/pool.py` | Нет холодного старта |
| 4 | Составной индекс | `db/migrations/003_...sql` | Быстрее cron воронки |

### Порядок реализации

1. Пул min_size=5 (1 строка, мгновенно)
2. Убрать дубль запросов (рефакторинг callbacks.py)
3. file_id кеш (основная работа в media.py)
4. Индекс БД (миграция)

### Тесты

- Обновить `test_callbacks.py` — хендлеры получают `language` из `data`, а не из `get_user_language`
- Добавить тесты для кеша file_id: первый вызов — скачивание, второй — из кеша
- Проверить что `send_local_photo` кеширует file_id после первой отправки
