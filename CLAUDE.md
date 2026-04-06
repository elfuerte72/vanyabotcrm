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

### Telegram Bot (`/bot`) — uv for dependency management
```bash
cd bot
uv sync                               # Install all deps (creates .venv automatically)
uv sync --no-dev                      # Install production deps only
uv run python -m src.main             # Start bot (polling + scheduler + webhook)
uv run pytest tests/ -v               # Run all tests (~456 tests)
uv run pytest tests/test_calculator.py  # Run single test file
uv run python -m scripts.trigger_funnel  # Manually trigger funnel sender
uv add <package>                      # Add dependency (updates pyproject.toml + uv.lock)
uv add --dev <package>                # Add dev dependency
```

### Database
```bash
# Connection string from DATABASE_URL env var
psql "$DATABASE_URL"
# Schema reference: db/schema.sql
# Migrations: db/migrations/ (sequential SQL files, applied manually)
```

### Funnel Testing Scripts (`/scripts/`, `/scripts_en/`, `/scripts_ar/`)
```bash
./scripts/run.sh belly/stage_0.py    # Send RU belly funnel stage to test user
./scripts/run.sh belly/reset.py      # Reset test user RU funnel state
./scripts_en/run.sh stage_0.py       # Send EN funnel stage message to test user
./scripts_ar/run.sh stage_0.py       # Send AR funnel stage message to test user
# RU scripts organized by zone variant: scripts/belly/, scripts/thighs/, etc.
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

**Telegram Bot** (`/bot`): Python 3.11+ / aiogram 3.x. AI nutrition consultant that collects user data via conversation (Gemini 3 Flash via OpenRouter), calculates KBJU (Harris-Benedict), generates meal plans, and runs a sales funnel. Supports RU/EN/AR languages. Entry point: `src/main.py` starts 3 concurrent services: polling + APScheduler (funnel sender every 15 min) + aiohttp webhook server (Ziina payments on port 8080).

**Deployment**: Both services deploy on Railway. CRM: `crm/railway.toml` (build: `npm run build`, start: `npm start`, health check: `/health`). Bot: `bot/railway.toml` (build: `uv sync --no-dev`, start: `uv run python -m src.main`). Database is on Supabase (project: `dnzwpdcvrpfiipjwpxux`).

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

**Subscription check** (`src/middlewares/subscription.py`): Checks channel membership (`@ivanfit_health` or numeric fallback `-1002504147240`) before processing messages. Only checks `Message` events, not callbacks. Only enforced for **RU users** — EN/AR users skip the check. **Currently disabled** in `src/bot.py` (commented out, pending bot admin access to channel).

**Funnel system**: RU funnel has **13 stages (0→12)** with zone branching. After meal plan delivery, bot sends two messages: "Разбуди тело" (wakeup with Yandex Disk URL) + zone selection (4 buttons: belly/thighs/arms/glutes) with 5-sec delay. Zone selection repeats every 24h until user picks. Zone callback (`zone_*`) sets `funnel_variant`, sends instant response, advances to stage 1 (+1h). Stages 1-12 are zone-specific (only `belly` variant implemented). EN and AR funnels have **11 stages (0→10)**: 9 main stages (0-8) with buy + question buttons, plus 2 upsells (9-10) after purchase. Timing: 5min after stage 0, 1h for stages 1-8, 24h for upsell stage 9. The scheduler (every 15 min) checks `next_funnel_msg_at` column and sends messages when the time has arrived. Timing logic is in `src/db/queries.py:calculate_next_send_time()` — RU messages are scheduled at specific Moscow times (10:00, 19:00 MSK), while EN/AR use interval delays (5min/1h/24h). Batch sending: 25 messages per batch with 1-second delay between batches (Telegram rate limit). Stage is incremented *after* sending, so callback buttons from stage N arrive when user is already at stage N+1.

**Media** (`config/media.yaml` + `bot/media/photos/`): RU funnel messages include local photos (`photo_name` field), media groups (`extra_photos` for album stages 2 and 9), and video notes (circles from Google Drive via `video_note_id`). EN and AR funnels include photos at stages 0 and 6 (shared `en_stage_0`/`en_stage_6` photos) plus question buttons for instant next-stage delivery. Video notes are sent as separate messages after the main content.

## Bot Testing Patterns

Tests use pytest + pytest-asyncio (`asyncio_mode = "auto"`) in `bot/tests/`. Env vars are set in `conftest.py` (fake `BOT_TOKEN`, `DATABASE_URL`, `OPENROUTER_API_KEY`) to prevent `Settings` validation errors. No database or API mocking needed for unit tests — calculator, language detection, formatter, funnel messages, and i18n are all pure functions. Test helpers in `tests/helpers.py` provide `make_bot`, `make_message`, `make_user`, `AGENT_RESPONSES`, `MEAL_PLANS`.

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

Default sort (no `sort` param): `updated_at DESC NULLS LAST, created_at DESC`.

## Database

**Connection**: PostgreSQL connection string in `DATABASE_URL` env var. Schema reference: `db/schema.sql`.

### Key Tables

**`users_nutrition`** — User profiles with nutrition data. PK: `chat_id` (bigint, Telegram ID). Key columns: `username`, `first_name`, `sex`, `age`, `weight`, `height`, `activity_level`, `goal` (weight_loss/weight_gain/maintenance/muscle_gain), `calories`/`protein`/`fats`/`carbs`, `funnel_stage` (0-12 for RU, 0-10 for EN/AR), `funnel_variant` (belly/thighs/arms/glutes/NULL — zone for RU branching), `is_buyer`, `get_food`, `language`, `id_ziina`, `type_ziina`, `funnel_start_at`, `last_funnel_msg_at`, `next_funnel_msg_at` (UTC, calculated by `calculate_next_send_time()`).

**`chat_histories`** — Chat messages. PK: `id` (auto-increment). `session_id` = chat_id as string. `message` is JSONB with `type` (human/ai), `content`, `tool_calls`.

**`user_events`** — Button clicks and funnel events. Columns: `id`, `chat_id`, `event_type`, `event_data`, `language`, `workflow_name`, `created_at`. Used in CRM to show full user interaction timeline alongside chat messages.

### Database Triggers

`users_nutrition` has NOTIFY triggers (`trg_clients_notify_ins/upd/del` → `notify_clients_changed()`) for real-time updates. Schema is exported in `db/schema.sql`. Always check for unexpected triggers before debugging data issues: `SELECT trigger_name, event_manipulation, action_statement FROM information_schema.triggers WHERE event_object_table = 'users_nutrition';`

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

## Related Documentation

- `AGENTS.md` — AI agent project map
- `db/migrations/` — 5 sequential migrations (rename chat_histories, funnel timing, scheduler index, upsell price types, funnel_variant)
- `new_ru(низ_живота).md` — RU belly zone funnel content spec (ТЗ)
- `ушки_на_бедрах.md` — RU thighs zone funnel content spec (ТЗ)

## Security Notes

- **Never hardcode credentials** in source files or CLAUDE.md — use `DATABASE_URL` env var
- CRM CORS: disabled in production (same-origin SPA), allows `localhost:5173` in dev
- SSL verification enabled (system CA) in both CRM and bot; `sslmode=disable` in DSN disables SSL for local dev
- Ziina webhook signature validation is mandatory — if `ZIINA_WEBHOOK_SECRET` is empty, webhooks return 503
- Auth is skipped when `BOT_TOKEN` is unset in dev; in production (`NODE_ENV=production`) missing `BOT_TOKEN` throws at startup
- CRM uses `helmet` for security headers, `express-rate-limit` (100 req/min on `/api`), and `zod` for input validation
- CRM uses `pino` + `pino-http` for structured logging (`LOG_LEVEL` env var, default: `info`)
