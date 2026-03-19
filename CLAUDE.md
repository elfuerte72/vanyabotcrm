# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

### CRM (`/crm`) — unified TypeScript project (server + client)
```bash
cd crm
npm run dev           # Concurrently: server (tsx watch :3001) + client (Vite :5173)
npm run dev:server    # Server only with hot reload (tsx watch, port 3001)
npm run dev:client    # Vite dev server (port 5173), proxies /api → localhost:3001
npm run build         # Build client (Vite) → build server (tsc) → copy client to server/public
npm start             # Run compiled server: node dist/server/index.js
npm test              # Run all tests (vitest run)
npm run test:watch    # Watch mode (vitest)
```

### Telegram Bot (`/bot`)
```bash
cd bot && source .venv/bin/activate
python -m src.main                    # Start bot (polling + scheduler + webhook)
python -m pytest tests/ -v            # Run all tests (340 tests)
python -m pytest tests/test_calculator.py  # Run single test file
python -m scripts.trigger_funnel      # Manually trigger funnel sender
```

### Database
```bash
# Connection string from DATABASE_URL env var
psql "$DATABASE_URL"
# Schema reference: db/schema.sql
```

No lint commands are configured.

## Architecture

```
Telegram Bot (aiogram) ──→ PostgreSQL
                          ↕
Telegram Mini App → React Client (Vite) → Express API ──→ PostgreSQL
```

Two services share the same PostgreSQL database:

**CRM** (`/crm`): Modular monolith — Express API + React SPA in a single TypeScript project. Shared types between server and client in `shared/`. Server modules in `server/modules/{users,chat,stats,events}/routes.ts`. Client is a Telegram Mini App with two views (list/detail) and two tabs (clients/recent). `server/app.ts` creates Express app; `server/index.ts` calls `app.listen()` (split for supertest). Auth middleware in `server/auth.ts` validates Telegram `initData`. In production, server serves client SPA via catch-all `*` route from `public/`.

**Telegram Bot** (`/bot`): Python 3.11+ / aiogram 3.x. AI nutrition consultant that collects user data via conversation (Gemini 3 Flash via OpenRouter), calculates KBJU (Mifflin-St Jeor), generates meal plans, and runs a 5-day sales funnel. Supports RU/EN/AR languages. Entry point: `src/main.py` starts polling + APScheduler (daily funnel at 23:00 UTC) + aiohttp webhook server (Ziina payments on port 8080).

**Deployment**: Bot deploys to Railway with NIXPACKS builder. CRM deployment is being migrated. Database is on Supabase.

## CRM Architecture (`/crm`)

```
crm/
├── shared/              # Shared types and constants (server + client)
│   ├── types.ts         # User, ChatMessage, UserEvent, Stats, UserFilters
│   └── constants.ts     # goalLabels, activityLabels, eventButtonLabels
├── server/              # Express API
│   ├── app.ts           # Express app (routes, middleware, static)
│   ├── index.ts         # Entry point: app.listen()
│   ├── auth.ts          # Telegram initData auth middleware
│   ├── db.ts            # PostgreSQL pool (SSL, no hardcoded fallback)
│   ├── modules/
│   │   ├── users/routes.ts    # GET /api/users, /api/users/recent, /api/users/:chatId
│   │   ├── chat/routes.ts     # GET /api/chat/:sessionId
│   │   ├── stats/routes.ts    # GET /api/stats
│   │   └── events/routes.ts   # GET /api/events/:chatId
│   └── __tests__/       # vitest + supertest tests
├── client/              # React SPA (Telegram Mini App)
│   ├── App.tsx          # Main app (list/detail views, clients/recent tabs)
│   ├── components/      # UI components (UserList, UserDetail, UserCard, etc.)
│   │   └── ui/          # shadcn/ui base components
│   ├── hooks/useApi.ts  # API hooks (re-exports types from shared/)
│   ├── lib/utils.ts     # cn() helper
│   ├── index.css        # Tailwind + CSS vars
│   └── vite-env.d.ts    # Telegram WebApp type declarations
├── package.json         # Unified deps (server + client)
├── tsconfig.json        # Client tsconfig (noEmit, JSX, @/ alias → ./client/)
├── tsconfig.server.json # Server tsconfig (commonjs, outDir → dist/server/)
├── vite.config.ts       # Vite (client build + dev proxy)
├── vitest.config.ts     # Test config
└── tailwind.config.js   # ESM config (never use require!)
```

### Dependency Rules
- ✅ `server/modules/*` → `server/db.ts`, `shared/*`
- ✅ `client/components/*` → `client/hooks/*`, `client/lib/*`, `shared/*`
- ❌ `server/` → `client/` (server must not import client code)
- ❌ `client/` → `server/` (client must not import server code)
- ❌ `shared/` → `server/` or `client/` (shared has no layer dependencies)

## Bot Architecture (`/bot`)

```
src/main.py          → Entry point: polling + scheduler + webhook server
src/bot.py           → Factory: creates Bot + Dispatcher, registers routers/middlewares
src/handlers/        → Telegram event handlers (start, message, callbacks, payment)
src/middlewares/     → Middleware chain: logging → subscription check → user data loading
src/services/        → Business logic (AI agents, calculator, formatter, language, media)
src/funnel/          → Sales funnel: message definitions, batch sender, scheduler
src/i18n/            → Localized strings per language (ru.py, en.py, ar.py)
src/db/              → asyncpg pool + all SQL queries
src/models/          → User dataclass
config/              → Pydantic Settings (.env) + media.yaml (Google Drive file IDs)
```

**Message flow** (`src/handlers/message.py`): Text/voice → detect language → AGENT MAIN (conversation or data collection) → if data ready: calculate KBJU → save to DB → AGENT FOOD (meal plan JSON) → validate → format HTML → send.

**Config** (`config/settings.py`): Uses lazy initialization via proxy objects — `settings` and `media_config` are not instantiated at import time. This allows tests to run without a `.env` file by setting env vars in `conftest.py`.

**Chat history**: Bot reads/writes to `chat_histories` table. `session_id` = `str(chat_id)`, `message` is JSONB with `type` (human/ai) and `content`.

**Subscription check** (`src/middlewares/subscription.py`): Checks channel membership (`@ivanfit_health` or numeric fallback `-1002504147240`) before processing messages. Only checks `Message` events, not callbacks. Allowed statuses: `member`, `administrator`, `creator`. Blocks handler if not subscribed — sends localized "please subscribe" message. If check fails (bot not admin), defaults to blocking.

**Funnel stages** (0→5): After user receives meal plan (`get_food=TRUE`), daily cron sends progressive sales messages. `get_funnel_targets()` fetches non-buyers with `funnel_stage` 0-4. Each send increments `funnel_stage` by 1. Important: stage is incremented by scheduler *after* sending, so when user clicks a callback button from stage N message, they are already at stage N+1.

## Bot Testing Patterns

Tests use pytest + pytest-asyncio in `bot/tests/`. Env vars are set in `conftest.py` (fake `BOT_TOKEN`, `DATABASE_URL`, `OPENROUTER_API_KEY`) to prevent `Settings` validation errors. No database or API mocking needed for unit tests — calculator, language detection, formatter, funnel messages, and i18n are all pure functions.

## API Endpoints

| Endpoint | Query Params |
|----------|-------------|
| `GET /api/users` | `search`, `status` (buyer/lead), `goal`, `funnel_stage`, `sort` (name/calories/funnel/age/weight), `order` (asc/desc) |
| `GET /api/users/recent` | `days` (1-365, default 7), `limit` (1-100, default 20) |
| `GET /api/users/:chatId` | — |
| `GET /api/stats` | — |
| `GET /api/chat/:sessionId` | — |
| `GET /api/events/:chatId` | `type` (filter by event_type) |
| `GET /health` | No auth required |

Auth: `Authorization: tma <initData>` header (1hr expiry).

Default sort (no `sort` param): `is_buyer DESC, funnel_stage DESC, first_name`.

## Database

**Connection**: PostgreSQL connection string in `DATABASE_URL` env var. Schema reference: `db/schema.sql`.

### Key Tables

**`users_nutrition`** — User profiles with nutrition data. PK: `chat_id` (bigint, Telegram ID). Key columns: `username`, `first_name`, `sex`, `age`, `weight`, `height`, `activity_level`, `goal` (weight_loss/weight_gain/maintenance/muscle_gain), `calories`/`protein`/`fats`/`carbs`, `funnel_stage` (0-6), `is_buyer`, `get_food`, `language`, `id_ziina`, `type_ziina`.

**`chat_histories`** — Chat messages (renamed from `n8n_chat_histories`). PK: `id` (auto-increment). `session_id` = chat_id as string. `message` is JSONB with `type` (human/ai), `content`, `tool_calls`.

**`user_events`** — Button clicks and funnel events. Columns: `id`, `chat_id`, `event_type`, `event_data`, `language`, `workflow_name`, `created_at`. Used in CRM to show full user interaction timeline alongside chat messages.

### Database Triggers

`users_nutrition` has NOTIFY triggers (`trg_clients_notify_ins/upd/del` → `notify_clients_changed()`) for real-time updates. Schema is exported in `db/schema.sql`. Always check for unexpected triggers before debugging data issues: `SELECT trigger_name, event_manipulation, action_statement FROM information_schema.triggers WHERE event_object_table = 'users_nutrition';`

## n8n Migration Status

The project has fully migrated away from n8n. The table `n8n_chat_histories` has been renamed to `chat_histories` (migration: `db/migrations/001_rename_chat_histories.sql`). A backward-compatible view `n8n_chat_histories` exists during transition. No n8n workflows are in use.

## Frontend Patterns

- **UI library**: shadcn/ui components in `client/components/ui/` (Card, Badge, Button, Tabs, Separator, Avatar) built on Radix UI primitives + class-variance-authority (CVA)
- **Icons**: Lucide React (`lucide-react`) — no inline SVGs
- **Utility**: `cn()` from `client/lib/utils.ts` (clsx + tailwind-merge) for conditional class merging
- **Path alias**: `@/` maps to `client/` (configured in both `vite.config.ts` and `tsconfig.json`)
- **Shared types/constants**: Defined in `shared/types.ts` and `shared/constants.ts`, re-exported from `client/hooks/useApi.ts`
- Hooks: `useUsers(filters)`, `useUser(chatId)`, `useStats()`, `useChatHistory(sessionId)`, `useUserEvents(chatId)`, `useRecentUsers(days, limit)`, `useDebounce(value, delay)`
- `useDebounce` default 300ms for search input
- **No animations or hover effects** — this is a mobile Telegram Mini App. Use `active:` states for touch feedback only
- `text-[16px]` on inputs prevents iOS auto-zoom
- `HapticFeedback` available via `window.Telegram.WebApp.HapticFeedback`
- Safe area insets handled via `--safe-area-top`/`--safe-area-bottom` CSS vars

### Color System

Dark theme with Anthropic-inspired palette. Colors use HSL CSS variables in space-separated format (e.g., `--primary: 28 48% 64%`) consumed by Tailwind via `hsl(var(--name) / <alpha-value>)` for opacity modifier support. Legacy `tg-*` tokens (hex values) are preserved for Telegram SDK compatibility but shadcn semantic tokens (`background`, `foreground`, `card`, `primary`, `secondary`, `muted`, `accent`, `destructive`) are the primary color system.

**Important**: `tailwind.config.js` uses ESM (`import`/`export default`). Never use `require()` in this file — it silently breaks the config.

## CRM Testing Patterns

Tests use Vitest + Supertest in `crm/server/__tests__/`. Database is mocked via `vi.mock('../db')` — mock `pool.query` return values rather than hitting the real database. Import `app` from `../app` (not `../index`) for supertest. Auth is automatically skipped in tests because `BOT_TOKEN` is unset.

## Railway Project

- **Project Name:** my n8n
- **Project ID:** 1f29c8b0-a81e-4d12-96cd-f97f87e96a16
- **Environment:** production
- **Active services:** Redis, Postgres (n8n), Worker, Primary (n8n instances)
- Bot and CRM services have been removed from Railway

## Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `PORT` | crm | Server port (default: 3001) |
| `BOT_TOKEN` | crm, bot | Telegram bot token |
| `DATABASE_URL` | crm, bot | Supabase PostgreSQL connection string |
| `VITE_API_URL` | crm | API base URL (empty = relative URLs with Vite proxy) |
| `CHANNEL_ID` | bot | Telegram channel ID for subscription check (default: -1002504147240) |
| `CHANNEL_USERNAME` | bot | Telegram channel username, preferred over ID (default: ivanfit_health) |
| `OPENROUTER_API_KEY` | bot | OpenRouter API key for AI agents |
| `OPENROUTER_MODEL` | bot | LLM model (default: google/gemini-3-flash-preview) |
| `TRIBUTE_LINK` | bot | Payment link for Tribute (RU users) |
| `ZIINA_LINK` | bot | Payment link for Ziina (EN/AR users, falls back to TRIBUTE_LINK) |
| `ZIINA_WEBHOOK_SECRET` | bot | Ziina payment webhook secret (optional) |
| `LOG_LEVEL` | crm, bot | Logging level (CRM default: info, Bot default: INFO) |
| `NODE_ENV` | crm | Environment (production requires BOT_TOKEN) |

## Security Notes

- **Never hardcode credentials** in source files or CLAUDE.md — use `DATABASE_URL` env var
- CRM CORS: disabled in production (same-origin SPA), allows `localhost:5173` in dev
- SSL verification enabled (system CA) in both CRM and bot; `sslmode=disable` in DSN disables SSL for local dev
- Ziina webhook signature validation is mandatory — if `ZIINA_WEBHOOK_SECRET` is empty, webhooks return 503
- Auth is skipped when `BOT_TOKEN` is unset in dev; in production (`NODE_ENV=production`) missing `BOT_TOKEN` throws at startup
- CRM uses `helmet` for security headers, `express-rate-limit` (100 req/min on `/api`), and `zod` for input validation
- CRM uses `pino` + `pino-http` for structured logging (`LOG_LEVEL` env var, default: `info`)
