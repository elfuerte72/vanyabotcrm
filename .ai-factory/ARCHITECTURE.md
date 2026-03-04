# Architecture: Layered Architecture

## Overview
Проект использует многослойную архитектуру (Layered Architecture) с тремя независимыми сервисами, каждый из которых организован по горизонтальным слоям. Все сервисы разделяют одну PostgreSQL базу данных на Railway, при этом бот записывает данные, а CRM (backend + frontend) читает их.

Этот паттерн выбран потому что: маленькая команда (1-2 разработчика), каждый сервис имеет простую предметную область, и проект уже естественно следует этому паттерну.

## Decision Rationale
- **Project type:** Telegram бот + Mini App CRM
- **Tech stack:** Python/aiogram (bot), TypeScript/Express (backend), React/Vite (frontend)
- **Key factor:** Проект уже следует layered-паттерну; формализация существующей архитектуры без unnecessary refactoring

## Folder Structure

### Bot (Python / aiogram)
```
bot/src/
├── handlers/           # Presentation: Telegram event handlers (routes)
│   ├── start.py        #   /start command
│   ├── message.py      #   Text/voice messages
│   ├── callbacks.py    #   Inline button callbacks
│   └── payment.py      #   Payment webhooks
├── middlewares/         # Cross-cutting: logging, auth, data loading
├── services/           # Business Logic: AI agents, calculator, formatter
│   ├── ai_agent.py     #   OpenRouter AI conversation
│   ├── calculator.py   #   KBJU calculation (Mifflin-St Jeor)
│   ├── formatter.py    #   HTML message formatting
│   ├── language.py     #   Language detection
│   └── media.py        #   Google Drive media serving
├── funnel/             # Business Logic: sales funnel
│   ├── messages.py     #   Funnel message definitions (stages 0-5)
│   ├── sender.py       #   Batch message sender
│   └── scheduler.py    #   APScheduler cron setup
├── i18n/               # Cross-cutting: localization strings
│   ├── ru.py
│   ├── en.py
│   └── ar.py
├── db/                 # Data Access: asyncpg queries
│   ├── pool.py         #   Connection pool management
│   └── queries.py      #   All SQL queries
├── models/             # Data Models: dataclasses
│   └── user.py
├── bot.py              # Composition root: Bot + Dispatcher factory
└── main.py             # Entry point: polling + scheduler + webhook
```

### Backend (TypeScript / Express)
```
backend/src/
├── routes/             # Presentation: HTTP route handlers
│   ├── users.ts        #   /api/users, /api/users/:chatId
│   ├── chat.ts         #   /api/chat/:sessionId
│   ├── stats.ts        #   /api/stats
│   └── events.ts       #   /api/events/:chatId
├── auth.ts             # Cross-cutting: Telegram initData middleware
├── db.ts               # Data Access: PostgreSQL pool (pg)
├── app.ts              # Composition root: Express app config
└── index.ts            # Entry point: app.listen()
```

### Frontend (React / TypeScript)
```
frontend/src/
├── components/         # Presentation: UI components
│   ├── ui/             #   shadcn/ui base (Card, Badge, Button, etc.)
│   ├── UserList.tsx    #   Client list with search/filters
│   ├── UserDetail.tsx  #   Full user profile + chat + events
│   └── ...
├── hooks/              # Data Access: API hooks
│   └── useApi.ts       #   All hooks, types, shared constants
├── lib/                # Utilities
│   └── utils.ts        #   cn() helper
└── App.tsx             # Composition root: routing + state
```

## Dependency Rules

### Bot
- ✅ `handlers/` → `services/`, `db/`, `i18n/`, `models/`
- ✅ `services/` → `db/`, `models/`
- ✅ `funnel/` → `db/`, `i18n/`, `models/`
- ✅ `middlewares/` → `db/`, `models/`
- ❌ `db/` → `handlers/`, `services/` (Data Access не знает о верхних слоях)
- ❌ `services/` → `handlers/` (бизнес-логика не знает о presentation)
- ❌ `models/` → что-либо кроме стандартной библиотеки

### Backend
- ✅ `routes/` → `db.ts`
- ✅ `routes/` → `auth.ts` (middleware)
- ❌ `db.ts` → `routes/`

### Frontend
- ✅ `components/` → `hooks/useApi.ts`, `lib/utils.ts`, `components/ui/`
- ✅ `App.tsx` → `components/`, `hooks/`
- ❌ `hooks/` → `components/` (data layer не знает о UI)
- ❌ `components/ui/` → `hooks/` (базовые UI компоненты не обращаются к API)

## Layer Communication

### Bot layers
```
Telegram Update → middlewares → handlers → services → db → PostgreSQL
                                   ↓
                                 i18n (localized strings)
```

### Backend layers
```
HTTP Request → auth middleware → route handler → db.query() → PostgreSQL
```

### Frontend layers
```
User action → Component → useApi hook → fetch(/api/*) → Backend
```

### Cross-service data flow
```
Bot writes → PostgreSQL ← Backend reads → Frontend displays
```

## Key Principles

1. **Каждый сервис — отдельный деплой.** Bot, backend, frontend деплоятся независимо на Railway. Изменения в боте не требуют передеплоя CRM.

2. **Shared database, не shared code.** Сервисы общаются через PostgreSQL, а не через прямые вызовы. Таблицы `users_nutrition`, `n8n_chat_histories`, `user_events` — это контракт между сервисами.

3. **Handlers не содержат бизнес-логику.** Handlers/routes только маршрутизируют запросы и форматируют ответы. Логика — в `services/` (bot) или инлайн в route handlers (backend, где логики мало).

4. **Pure functions where possible.** Калькулятор, форматтер, language detection, i18n строки — чистые функции без side effects. Это упрощает тестирование.

5. **Config через environment.** Все credentials и настройки — через переменные окружения. Pydantic Settings (bot) и `process.env` (backend).

## Code Examples

### Bot: Handler → Service → DB (правильная зависимость)
```python
# handlers/message.py — Presentation layer
async def handle_message(message: Message, user: User):
    lang = detect_language(message.text)          # service (pure)
    response = await ai_agent.process(message.text, user)  # service
    await save_message(user.chat_id, response)    # db
    await message.answer(response)

# services/calculator.py — Business Logic (pure function, no DB)
def calculate_kbju(sex: str, weight: float, height: float, age: int,
                   activity: float, goal: str) -> dict:
    bmr = (10 * weight + 6.25 * height - 5 * age)
    bmr += 5 if sex == "male" else -161
    tdee = bmr * activity
    # ... goal adjustments
    return {"calories": round(tdee), "protein": ..., "fats": ..., "carbs": ...}

# db/queries.py — Data Access (only SQL, no business logic)
async def update_user_nutrition(chat_id: int, data: dict):
    await pool.execute(
        "UPDATE users_nutrition SET calories=$1, protein=$2 WHERE chat_id=$3",
        data["calories"], data["protein"], chat_id
    )
```

### Backend: Route → DB (simple layered)
```typescript
// routes/users.ts — Presentation + Data Access (acceptable for thin backend)
router.get('/api/users', authMiddleware, async (req, res) => {
  const { search, status, sort, order } = req.query;
  // Build query (light logic inline — no separate service needed)
  let query = 'SELECT * FROM users_nutrition WHERE 1=1';
  if (search) query += ` AND first_name ILIKE $1`;
  const result = await pool.query(query, params);
  res.json(result.rows);
});
```

### Frontend: Component → Hook (data flow)
```tsx
// components/UserList.tsx — Presentation (no fetch logic)
function UserList({ onSelect }: Props) {
  const { data: users } = useUsers(filters);  // hook handles fetching
  return users?.map(u => <UserCard key={u.chat_id} user={u} />);
}

// hooks/useApi.ts — Data Access
function useUsers(filters: UserFilters) {
  const params = new URLSearchParams();
  if (filters.search) params.set('search', filters.search);
  return useFetch<User[]>(`/api/users?${params}`);
}
```

## Anti-Patterns

- ❌ **DB queries в handlers.** Не пишите SQL напрямую в Telegram handlers бота — используйте `db/queries.py`. Backend это исключение (thin layer, inline queries допустимы).
- ❌ **Бизнес-логика в middleware.** Middleware только для cross-cutting concerns: логирование, аутентификация, загрузка данных пользователя.
- ❌ **Import между сервисами.** Bot, backend и frontend не импортируют код друг друга. Единственный shared контракт — схема БД.
- ❌ **Frontend вызывает БД напрямую.** Все данные проходят через backend API. Frontend никогда не обращается к PostgreSQL.
- ❌ **Hardcoded credentials.** Все секреты через переменные окружения, никогда в коде.
