# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

### Backend (`/backend`)
```bash
npm run dev          # Dev server with hot reload (tsx watch, port 3001)
npm run build        # Compile TypeScript → dist/
npm start            # Run compiled server
```

### Frontend (`/frontend`)
```bash
npm run dev          # Vite dev server (port 5173), proxies /api → localhost:3001
npm run build        # tsc + vite build → dist/
npm run preview      # Preview production build
```

### Backend Tests (`/backend`)
```bash
npm test             # Run all tests (vitest run)
npm run test:watch   # Watch mode (vitest)
npx vitest run src/__tests__/chat.test.ts  # Run a single test file
```

### Telegram Bot (`/bot`)
```bash
cd bot && source .venv/bin/activate
python -m src.main                    # Start bot (polling + scheduler + webhook)
python -m pytest tests/ -v            # Run all tests (58 tests)
python -m pytest tests/test_calculator.py  # Run single test file
python -m scripts.trigger_funnel      # Manually trigger funnel sender
```

### Database
```bash
PGPASSWORD='y6G7oBq6-0VdfPV3S6HuliVFeL2d4tMa' psql -h yamabiko.proxy.rlwy.net -p 26903 -U railway -d railway
```

No lint commands are configured.

## Architecture

```
Telegram Bot (aiogram) ──→ PostgreSQL (Railway)
                          ↕
Telegram Mini App → React Frontend (Vite) → Express API ──→ PostgreSQL (Railway)
```

Three services share the same PostgreSQL database:

**Frontend** (`/frontend/src`): React 18 + TypeScript + Tailwind CSS + shadcn/ui components. Single-page app with two views (list/detail) and two tabs (clients/recent) switched via state in `App.tsx`. All API hooks and types live in `hooks/useApi.ts`. No routing library. UI labels are in Russian. Mobile-first Telegram Mini App — no hover effects, no animations.

**Backend** (`/backend/src`): Express + TypeScript. `app.ts` creates the Express app (routes, middleware, static serving); `index.ts` only calls `app.listen()`. This split enables supertest to import `app.ts` directly without starting a server. Routes in `src/routes/` — `users.ts`, `chat.ts`, `stats.ts`, `events.ts`. Database pool in `db.ts` (SSL with `rejectUnauthorized: false`). Auth middleware validates Telegram `initData` via `@telegram-apps/init-data-node`. Auth skipped when `BOT_TOKEN` env is unset (dev mode). In production, backend also serves the frontend SPA via a catch-all `*` route from `public/`.

**Telegram Bot** (`/bot`): Python 3.11+ / aiogram 3.x. AI nutrition consultant that collects user data via conversation (Gemini 3 Flash via OpenRouter), calculates KBJU (Mifflin-St Jeor), generates meal plans, and runs a 5-day sales funnel. Supports RU/EN/AR languages. Entry point: `src/main.py` starts polling + APScheduler (daily funnel at 23:00 UTC) + aiohttp webhook server (Ziina payments on port 8080).

**Deployment**: All services deploy to Railway with NIXPACKS builder.

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

**Chat history**: Bot reads/writes to `n8n_chat_histories` table (backward-compatible with n8n format). `session_id` = `str(chat_id)`, `message` is JSONB with `type` (human/ai) and `content`.

**Funnel stages** (0→5): After user receives meal plan (`get_food=TRUE`), daily cron sends progressive sales messages. `get_funnel_targets()` fetches non-buyers with `funnel_stage` 0-4. Each send increments `funnel_stage` by 1.

## Bot Testing Patterns

Tests use pytest + pytest-asyncio in `bot/tests/`. Env vars are set in `conftest.py` (fake `BOT_TOKEN`, `DATABASE_URL`, `OPENROUTER_API_KEY`) to prevent `Settings` validation errors. No database or API mocking needed for unit tests — calculator, language detection, formatter, funnel messages, and i18n are all pure functions.

## API Endpoints

| Endpoint | Query Params |
|----------|-------------|
| `GET /api/users` | `search`, `status` (buyer/lead), `goal`, `funnel_stage`, `sort` (name/calories/funnel/age/weight), `order` (asc/desc) |
| `GET /api/users/:chatId` | — |
| `GET /api/stats` | — |
| `GET /api/chat/:sessionId` | — |
| `GET /api/events/:chatId` | `type` (filter by event_type) |
| `GET /health` | No auth required |

Auth: `Authorization: tma <initData>` header (1hr expiry).

Default sort (no `sort` param): `is_buyer DESC, funnel_stage DESC, first_name`.

## Database

**Connection**: `postgres://railway:y6G7oBq6-0VdfPV3S6HuliVFeL2d4tMa@yamabiko.proxy.rlwy.net:26903/railway`

### Key Tables

**`users_nutrition`** — User profiles with nutrition data. PK: `chat_id` (bigint, Telegram ID). Key columns: `username`, `first_name`, `sex`, `age`, `weight`, `height`, `activity_level`, `goal` (weight_loss/weight_gain/maintenance/muscle_gain), `calories`/`protein`/`fats`/`carbs`, `funnel_stage` (0-6), `is_buyer`, `get_food`, `language`, `id_ziina`, `type_ziina`.

**`n8n_chat_histories`** — Chat messages. PK: `id` (auto-increment). `session_id` = chat_id as string. `message` is JSONB with `type` (human/ai), `content`, `tool_calls`.

**`user_events`** — Button clicks and funnel events. Columns: `id`, `chat_id`, `event_type`, `event_data`, `language`, `workflow_name`, `created_at`. Used in CRM to show full user interaction timeline alongside chat messages.

## Frontend Patterns

- **UI library**: shadcn/ui components in `src/components/ui/` (Card, Badge, Button, Tabs, Separator, Avatar) built on Radix UI primitives + class-variance-authority (CVA)
- **Icons**: Lucide React (`lucide-react`) — no inline SVGs
- **Utility**: `cn()` from `src/lib/utils.ts` (clsx + tailwind-merge) for conditional class merging
- **Path alias**: `@/` maps to `src/` (configured in both `vite.config.ts` and `tsconfig.json`)
- Shared constants (`goalLabels`, `activityLabels`, `eventButtonLabels`) exported from `hooks/useApi.ts` — don't duplicate in components
- Hooks: `useUsers(filters)`, `useUser(chatId)`, `useStats()`, `useChatHistory(sessionId)`, `useUserEvents(chatId)`, `useRecentUsers(days, limit)`, `useDebounce(value, delay)`
- `useDebounce` default 300ms for search input
- **No animations or hover effects** — this is a mobile Telegram Mini App. Use `active:` states for touch feedback only
- `text-[16px]` on inputs prevents iOS auto-zoom
- `HapticFeedback` available via `window.Telegram.WebApp.HapticFeedback`
- Safe area insets handled via `--safe-area-top`/`--safe-area-bottom` CSS vars

### Color System

Dark theme with Anthropic-inspired palette. Colors use HSL CSS variables in space-separated format (e.g., `--primary: 28 48% 64%`) consumed by Tailwind via `hsl(var(--name) / <alpha-value>)` for opacity modifier support. Legacy `tg-*` tokens (hex values) are preserved for Telegram SDK compatibility but shadcn semantic tokens (`background`, `foreground`, `card`, `primary`, `secondary`, `muted`, `accent`, `destructive`) are the primary color system.

**Important**: `tailwind.config.js` uses ESM (`import`/`export default`). Never use `require()` in this file — it silently breaks the config.

## Backend Testing Patterns

Tests use Vitest + Supertest in `src/__tests__/`. Database is mocked via `vi.mock('../db')` — mock `pool.query` return values rather than hitting the real database. Import `app` from `../app` (not `../index`) for supertest. Auth is automatically skipped in tests because `BOT_TOKEN` is unset.

## Railway Project

- **Project Name:** my n8n
- **Project ID:** 1f29c8b0-a81e-4d12-96cd-f97f87e96a16
- **Environment:** production

## Environment Variables

| Variable | Service | Description |
|----------|---------|-------------|
| `PORT` | backend | Server port (default: 3001) |
| `BOT_TOKEN` | backend, bot | Telegram bot token |
| `DATABASE_URL` | backend, bot | PostgreSQL connection string |
| `VITE_API_URL` | frontend | API base URL (empty = relative URLs with Vite proxy) |
| `CHANNEL_ID` | bot | Telegram channel ID for subscription check |
| `OPENROUTER_API_KEY` | bot | OpenRouter API key for AI agents |
| `OPENROUTER_MODEL` | bot | LLM model (default: google/gemini-3-flash-preview) |
| `TRIBUTE_LINK` | bot | Payment link for Tribute |
| `LOG_LEVEL` | bot | Logging level (default: DEBUG) |
