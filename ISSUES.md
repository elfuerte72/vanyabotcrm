# Известные проблемы и план исправлений

> Последнее обновление: 2026-03-18

---

## КРИТИЧЕСКИЕ

### 1. Утечка credentials в git history
**Где:** `crm/server/db.ts`, `CLAUDE.md` (исправлен), `.mcp.json`, `.claude/settings.local.json`
**Суть:** Пароль БД захардкожен в fallback строке подключения и фигурирует в нескольких конфиг-файлах. Даже после удаления из кода — остаётся в git history.
**Действия:**
- [x] ~~Ротировать пароль PostgreSQL на Railway~~ — неактуально, мигрировали на Supabase
- [x] Убрать fallback connection string из `crm/server/db.ts` — если `DATABASE_URL` не задан, сервер не должен стартовать
- [ ] Очистить git history через BFG Repo-Cleaner или `git filter-repo`
- [ ] Ротировать OpenRouter API key
- [ ] Ротировать Telegram bot token через @BotFather

### 2. CORS принимает любой origin
**Где:** `crm/server/app.ts:14-17`
```typescript
app.use(cors({ origin: true, credentials: true }));
```
**Суть:** Любой сайт может делать authenticated-запросы к API и получать данные пользователей.
**Действия:**
- [ ] Ограничить `origin` списком разрешённых доменов (домен Mini App на Railway, `https://t.me`)

### 3. SSL-верификация отключена
**Где:** `crm/server/db.ts:6` (`rejectUnauthorized: false`), `bot/src/db/pool.py:31-32` (`CERT_NONE`)
**Суть:** Подключение к БД уязвимо к MITM-атакам — сертификат сервера не проверяется.
**Действия:**
- [ ] Проверить, поддерживает ли Supabase SSL с валидным сертификатом
- [ ] Если да — включить `rejectUnauthorized: true` и `ssl.CERT_REQUIRED`
- [ ] Если нет — задокументировать как принятый риск

### 4. Ziina webhook без обязательной подписи
**Где:** `bot/src/handlers/payment.py:27-47`
**Суть:** Если `ZIINA_WEBHOOK_SECRET` пуст, бот принимает любой webhook без проверки подписи. Атакующий может подделать payment confirmation и пометить пользователя как buyer.
**Действия:**
- [ ] Сделать `ZIINA_WEBHOOK_SECRET` обязательным — отклонять webhooks если секрет не настроен
- [ ] Логировать все попытки невалидных webhooks

---

## ВЫСОКИЙ ПРИОРИТЕТ

### 5. Нет rate limiting на API
**Где:** `crm/server/app.ts` — все роуты
**Суть:** Без ограничений можно выкачать всю базу пользователей или устроить DoS.
**Действия:**
- [ ] Добавить `express-rate-limit` — например 100 req/min на IP
- [ ] Отдельный более строгий лимит на `/api/users` с `search`

### 6. Auth полностью отключается без BOT_TOKEN
**Где:** `crm/server/app.ts:22-25`
**Суть:** Если переменная `BOT_TOKEN` не задана, middleware пропускает все запросы без аутентификации. Удобно для dev, но опасно если забыть выставить на production.
**Действия:**
- [ ] Добавить явную проверку `NODE_ENV` — в production требовать `BOT_TOKEN`
- [ ] При старте без `BOT_TOKEN` в production — не стартовать сервер

### 7. Нет валидации входных параметров
**Где:** `crm/server/modules/users/routes.ts`, `events/routes.ts`, `chat/routes.ts`
**Суть:** `chatId`, `funnel_stage`, `search` принимаются без проверки типа и границ. SQL-инъекции нет (параметризованные запросы), но возможны логические ошибки.
**Действия:**
- [ ] Валидировать `chatId` как числовой bigint
- [ ] Ограничить `funnel_stage` диапазоном 0-6
- [ ] Ограничить длину `search` (например, 100 символов)
- [ ] Рассмотреть `zod` для валидации query params

### 8. `.env` файлы могут попасть в git
**Где:** `.env`, `bot/.env`
**Суть:** `.gitignore` настроен, но если файлы уже были закоммичены ранее — они в history. Нужна проверка.
**Действия:**
- [ ] Проверить `git log --all --full-history -- .env bot/.env`
- [ ] Если найдены — очистить через BFG
- [ ] Добавить pre-commit hook, блокирующий коммит `.env` файлов

---

## СРЕДНИЙ ПРИОРИТЕТ

### 9. Нет миграций БД в репозитории
**Суть:** Таблицы `users_nutrition`, `n8n_chat_histories`, `user_events` создавались вручную. Нет файлов миграций, нет способа воссоздать схему с нуля. Триггеры (например `trg_clients_notify_*`) тоже не в коде.
**Действия:**
- [x] Выгрузить текущую схему: `pg_dump --schema-only`
- [x] Добавить в репо `db/schema.sql`
- [ ] Рассмотреть инструмент миграций (dbmate, golang-migrate, или Prisma)

### 10. Имя таблицы `n8n_chat_histories` — legacy
**Суть:** n8n больше не используется, но имя таблицы осталось. Путает новых разработчиков.
**Действия:**
- [ ] Переименовать в `chat_histories` (или `chat_messages`)
- [ ] Обновить все ссылки в `bot/src/db/queries.py` и `crm/server/modules/chat/routes.ts`

### 11. Railway project называется "my n8n"
**Суть:** Устаревшее название после отказа от n8n.
**Действия:**
- [ ] Переименовать проект на Railway

### 12. Нет HTTPS enforcement в backend
**Где:** `crm/server/app.ts`
**Суть:** Нет редиректа HTTP → HTTPS, нет HSTS заголовка.
**Действия:**
- [ ] Проверить, обеспечивает ли Railway HTTPS на уровне прокси
- [ ] Если нет — добавить `helmet` middleware с HSTS

### 13. Нет логирования для аудита
**Суть:** Backend не логирует запросы к API (кто запрашивал, какие данные). Невозможно расследовать инциденты.
**Действия:**
- [ ] Добавить structured logging (morgan или pino)
- [ ] Логировать: endpoint, user ID из initData, timestamp, status code

---

## НИЗКИЙ ПРИОРИТЕТ

### 15. Boolean литералы не параметризованы
**Где:** `crm/server/modules/users/routes.ts:27-30`
```typescript
conditions.push(`is_buyer = true`);  // литерал вместо параметра
```
**Суть:** Не уязвимость (значение контролируется кодом), но нарушает единообразие — все остальные условия используют `$N` параметры.
**Действия:**
- [ ] Заменить на параметризованные значения для consistency

### 16. Webhook endpoint без rate limiting
**Где:** `bot/src/handlers/payment.py` — `/webhook/ziina`
**Суть:** Спам на webhook может нагрузить бота.
**Действия:**
- [ ] Добавить rate limiting на aiohttp webhook server

### 17. Bot logging может содержать PII
**Где:** `bot/src/middlewares/logging.py`, `bot/src/handlers/message.py`
**Суть:** Debug логи могут содержать текст сообщений пользователей.
**Действия:**
- [ ] В production выставить `LOG_LEVEL=INFO` или выше
- [ ] Убедиться что `DEBUG` уровень не логирует content сообщений
