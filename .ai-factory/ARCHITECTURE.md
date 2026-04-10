# Architecture: Modular Monolith (Dual-Service)

## Overview
The project consists of two independent services — a Telegram Bot (Python/aiogram) and a CRM Mini App (TypeScript/Express+React) — that share a single PostgreSQL database as their integration contract. Each service is a modular monolith internally: the CRM organizes server logic into feature modules (`users`, `chat`, `stats`, `events`), while the bot separates concerns into layers (`handlers`, `services`, `middlewares`, `funnel`, `db`).

This architecture was chosen because both services are maintained by a single developer, share the same database, and deploy independently on Railway. A modular monolith provides clear boundaries without the operational overhead of microservices.

## Decision Rationale
- **Project type:** AI Telegram bot + admin CRM for fitness coaching
- **Tech stack:** Python 3.11 (bot) + TypeScript (CRM) + PostgreSQL (Supabase)
- **Team size:** 1 developer
- **Key factor:** Simple operations, shared database contract, independent deployment via Railway

## Folder Structure
```
monitoringsql/
├── bot/                            # Service 1: Telegram Bot (Python)
│   ├── src/
│   │   ├── main.py                 # Entry: polling + scheduler + webhook
│   │   ├── bot.py                  # Factory: Bot + Dispatcher
│   │   ├── handlers/               # Presentation: Telegram event handlers
│   │   │   ├── start.py            # /start command
│   │   │   ├── message.py          # Text/voice message processing
│   │   │   ├── callbacks.py        # Inline button callbacks
│   │   │   └── payment.py          # Payment webhook handlers
│   │   ├── middlewares/            # Cross-cutting: logging, auth, data loading
│   │   ├── services/               # Business logic layer
│   │   │   ├── ai_agents.py        # AI conversation (OpenRouter)
│   │   │   ├── calculator.py       # KBJU calculation (Harris-Benedict)
│   │   │   ├── formatter.py        # HTML message formatting
│   │   │   ├── language.py         # Language detection
│   │   │   └── media.py            # Media file handling
│   │   ├── funnel/                 # Domain: sales funnel
│   │   │   ├── messages_ru.py      # RU funnel content (zone-specific)
│   │   │   ├── messages_en.py      # EN funnel content
│   │   │   ├── messages_ar.py      # AR funnel content
│   │   │   ├── sender.py           # Batch message sender
│   │   │   └── scheduler.py        # APScheduler integration
│   │   ├── i18n/                   # Localization strings
│   │   ├── db/                     # Data access layer
│   │   │   ├── pool.py             # asyncpg connection pool
│   │   │   └── queries.py          # All SQL queries
│   │   └── models/                 # Data models (dataclasses)
│   ├── config/                     # Configuration (Pydantic Settings)
│   └── tests/                      # pytest tests
├── crm/                            # Service 2: CRM Mini App (TypeScript)
│   ├── shared/                     # Shared types (server ↔ client contract)
│   │   ├── types.ts                # User, ChatMessage, UserEvent, Stats
│   │   └── constants.ts            # Labels, enums
│   ├── server/                     # Express API (modular)
│   │   ├── app.ts                  # Express app setup
│   │   ├── index.ts                # Server entry point
│   │   ├── auth.ts                 # Telegram initData middleware
│   │   ├── db.ts                   # PostgreSQL pool
│   │   └── modules/                # Feature modules
│   │       ├── users/routes.ts     # User CRUD + filters
│   │       ├── chat/routes.ts      # Chat history
│   │       ├── stats/routes.ts     # Aggregated statistics
│   │       └── events/routes.ts    # User event timeline
│   └── client/                     # React SPA (Telegram Mini App)
│       ├── App.tsx                 # Root component
│       ├── components/             # UI components
│       ├── hooks/useApi.ts         # API hooks
│       └── lib/utils.ts            # Utilities
├── db/                             # Database contract (shared between services)
│   ├── schema.sql                  # Full schema (source of truth)
│   └── migrations/                 # Sequential SQL migrations
└── scripts/                        # Testing & utility scripts
```

## Dependency Rules

### Bot (Python)
- `handlers/` → `services/`, `db/`, `funnel/`, `i18n/`, `models/`
- `services/` → `db/`, `models/`, `config/`
- `funnel/` → `db/`, `services/`, `config/`
- `middlewares/` → `db/`, `models/`
- `db/` → `config/` (connection settings only)
- `models/` → nothing (pure data)
- `config/` → nothing (env vars only)

### CRM (TypeScript)
- `server/modules/*` → `server/db.ts`, `shared/*`
- `client/components/*` → `client/hooks/*`, `client/lib/*`, `shared/*`
- `shared/` → nothing (no layer dependencies)
- `server/` ↛ `client/` (server must not import client code)
- `client/` ↛ `server/` (client must not import server code)

### Cross-Service
- Bot ↛ CRM code (no direct imports)
- CRM ↛ Bot code (no direct imports)
- Both → `db/schema.sql` (shared database contract)

## Layer Communication

### Bot message flow
```
Telegram → Handler → Service (AI/Calculator) → DB → Formatter → Telegram
                  ↘ Middleware (logging, auth, data loading)
```

### CRM request flow
```
React Client → fetch(/api/*) → Express Route → SQL Query → JSON Response
                              → Auth Middleware (Telegram initData)
```

### Inter-service communication
```
Bot writes → PostgreSQL ← CRM reads
             NOTIFY triggers → real-time updates
```

Services communicate only through the shared database. PostgreSQL NOTIFY triggers on `users_nutrition` enable real-time CRM updates when the bot modifies user data.

## Key Principles

1. **Database as integration contract.** `db/schema.sql` is the single source of truth. Both services must be compatible with the current schema. Migrations are sequential SQL files applied manually.

2. **Feature modules in CRM.** Each server module (`users`, `chat`, `stats`, `events`) is self-contained with its own routes file. Modules share only `db.ts` and `shared/` types.

3. **Layered bot with domain isolation.** Funnel logic (messages, scheduling, sending) is isolated in `src/funnel/`. Business services (calculator, AI agents, formatter) are stateless and testable without database or API mocking.

4. **Lazy configuration.** Bot config uses proxy objects — `settings` and `media_config` are not instantiated at import time, allowing tests to run without `.env`.

5. **Shared types, not shared code.** CRM `shared/` directory defines TypeScript interfaces used by both server and client. No runtime code sharing between services.

## Code Examples

### Bot: Handler → Service → DB pattern
```python
# src/handlers/message.py
async def handle_message(message: Message, user_data: dict):
    lang = detect_language(message.text)           # services/language.py
    response = await run_agent(message.text, user_data)  # services/ai_agents.py
    
    if user_data_complete(response):
        kbju = calculate_kbju(user_data)           # services/calculator.py (pure)
        await save_nutrition(chat_id, kbju)         # db/queries.py
        meal_plan = await generate_meal_plan(kbju)  # services/ai_agents.py
        html = format_meal_plan(meal_plan)          # services/formatter.py (pure)
        await message.answer(html, parse_mode="HTML")
```

### CRM: Module route pattern
```typescript
// server/modules/users/routes.ts
import { Router } from 'express';
import { pool } from '../../db';
import type { User, UserFilters } from '../../../shared/types';

const router = Router();

router.get('/api/users', async (req, res) => {
  const filters: UserFilters = { /* validated from req.query */ };
  const { rows } = await pool.query<User>(sql, params);
  res.json(rows);
});

export default router;
```

### CRM: Client hook consuming shared types
```typescript
// client/hooks/useApi.ts
import type { User, UserFilters } from '../../shared/types';

export function useUsers(filters: UserFilters) {
  const [users, setUsers] = useState<User[]>([]);
  // fetch from /api/users with filters
  return { users, loading, error };
}
```

## Anti-Patterns

- **Cross-service imports.** Never import bot Python code from CRM TypeScript or vice versa. The database is the only integration point.
- **Direct DB access from client.** React client must always go through Express API routes, never query the database directly.
- **Skipping shared types.** Don't define the same interface separately in server and client — use `shared/types.ts`.
- **Hardcoded SQL in handlers.** Keep all SQL queries in `db/queries.py` (bot) or within module route files (CRM). Don't scatter queries across handlers/services.
- **Importing server internals across modules.** CRM modules should depend on `db.ts` and `shared/`, not on other modules' internal implementations.
- **Using `require()` in ESM config files.** `tailwind.config.js` and `vite.config.ts` use ESM — always use `import`/`export default`.
