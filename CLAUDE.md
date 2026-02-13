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

### Database
```bash
PGPASSWORD='y6G7oBq6-0VdfPV3S6HuliVFeL2d4tMa' psql -h yamabiko.proxy.rlwy.net -p 26903 -U railway -d railway
```

No lint commands are configured.

## Architecture

```
Telegram Mini App → React Frontend (Vite) → Express API → PostgreSQL (Railway)
```

**Frontend** (`/frontend/src`): React 18 + TypeScript + Tailwind CSS + shadcn/ui components. Single-page app with two views (list/detail) and two tabs (clients/recent) switched via state in `App.tsx`. All API hooks and types live in `hooks/useApi.ts`. No routing library. UI labels are in Russian. Mobile-first Telegram Mini App — no hover effects, no animations.

**Backend** (`/backend/src`): Express + TypeScript. `app.ts` creates the Express app (routes, middleware, static serving); `index.ts` only calls `app.listen()`. This split enables supertest to import `app.ts` directly without starting a server. Routes in `src/routes/` — `users.ts`, `chat.ts`, `stats.ts`. Database pool in `db.ts` (SSL with `rejectUnauthorized: false`). Auth middleware validates Telegram `initData` via `@telegram-apps/init-data-node`. Auth skipped when `BOT_TOKEN` env is unset (dev mode). In production, backend also serves the frontend SPA via a catch-all `*` route from `public/`.

**Deployment**: Both services deploy to Railway with NIXPACKS builder. Frontend serves static files via `npx serve dist`. Backend compiles TypeScript then runs `node dist/index.js`.

## API Endpoints

| Endpoint | Query Params |
|----------|-------------|
| `GET /api/users` | `search`, `status` (buyer/lead), `goal`, `funnel_stage`, `sort` (name/calories/funnel/age/weight), `order` (asc/desc) |
| `GET /api/users/:chatId` | — |
| `GET /api/stats` | — |
| `GET /api/chat/:sessionId` | — |
| `GET /health` | No auth required |

Auth: `Authorization: tma <initData>` header (1hr expiry).

Default sort (no `sort` param): `is_buyer DESC, funnel_stage DESC, first_name`.

## Database

**Connection**: `postgres://railway:y6G7oBq6-0VdfPV3S6HuliVFeL2d4tMa@yamabiko.proxy.rlwy.net:26903/railway`

### Key Tables

**`users_nutrition`** — User profiles with nutrition data. PK: `chat_id` (bigint, Telegram ID). Key columns: `username`, `first_name`, `sex`, `age`, `weight`, `height`, `activity_level`, `goal` (weight_loss/weight_gain/maintenance/muscle_gain), `calories`/`protein`/`fats`/`carbs`, `funnel_stage` (0-6), `is_buyer`, `get_food`, `language`, `id_ziina`, `type_ziina`.

**`n8n_chat_histories`** — Chat messages. PK: `id` (auto-increment). `session_id` = chat_id as string. `message` is JSONB with `type` (human/ai), `content`, `tool_calls`.

## Frontend Patterns

- **UI library**: shadcn/ui components in `src/components/ui/` (Card, Badge, Button, Tabs, Separator, Avatar) built on Radix UI primitives + class-variance-authority (CVA)
- **Icons**: Lucide React (`lucide-react`) — no inline SVGs
- **Utility**: `cn()` from `src/lib/utils.ts` (clsx + tailwind-merge) for conditional class merging
- **Path alias**: `@/` maps to `src/` (configured in both `vite.config.ts` and `tsconfig.json`)
- Shared constants (`goalLabels`, `activityLabels`) exported from `hooks/useApi.ts` — don't duplicate in components
- Hooks: `useUsers(filters)`, `useUser(chatId)`, `useStats()`, `useChatHistory(sessionId)`, `useRecentUsers(days)`, `useDebounce(value, delay)`
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
| `BOT_TOKEN` | backend | Telegram bot token for auth validation |
| `DATABASE_URL` | backend | PostgreSQL connection string |
| `VITE_API_URL` | frontend | API base URL (empty = relative URLs with Vite proxy) |
