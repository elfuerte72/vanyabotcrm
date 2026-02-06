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

### Database
```bash
PGPASSWORD='y6G7oBq6-0VdfPV3S6HuliVFeL2d4tMa' psql -h yamabiko.proxy.rlwy.net -p 26903 -U railway -d railway
```

No test or lint commands are configured.

## Architecture

```
Telegram Mini App → React Frontend (Vite) → Express API → PostgreSQL (Railway)
```

**Frontend** (`/frontend/src`): React 18 + TypeScript + Tailwind CSS. Single-page app with two views (list/detail) switched in `App.tsx`. All API hooks live in `hooks/useApi.ts`. Telegram theme colors mapped to `tg-*` Tailwind tokens. No routing library — state-driven view switching.

**Backend** (`/backend/src`): Express + TypeScript. Routes in `src/routes/` — `users.ts`, `chat.ts`, `stats.ts`. Database pool in `db.ts`. Auth middleware validates Telegram `initData` via `@telegram-apps/init-data-node`. Auth skipped when `BOT_TOKEN` env is unset (dev mode).

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

## Database

**Connection**: `postgres://railway:y6G7oBq6-0VdfPV3S6HuliVFeL2d4tMa@yamabiko.proxy.rlwy.net:26903/railway`

### Key Tables

**`users_nutrition`** — User profiles with nutrition data. PK: `chat_id` (bigint, Telegram ID). Key columns: `username`, `first_name`, `sex`, `age`, `weight`, `height`, `activity_level`, `goal` (weight_loss/weight_gain/maintenance/muscle_gain), `calories`/`protein`/`fats`/`carbs`, `funnel_stage` (0-6), `is_buyer`, `get_food`, `language`, `id_ziina`, `type_ziina`.

**`n8n_chat_histories`** — Chat messages. PK: `id` (auto-increment). `session_id` = chat_id as string. `message` is JSONB with `type` (human/ai), `content`, `tool_calls`.

## Frontend Patterns

- Shared constants (`goalLabels`, `activityLabels`) exported from `hooks/useApi.ts` — don't duplicate in components
- `useDebounce` hook (300ms) for search input
- `useUsers(filters: UserFilters)` builds query string and calls backend
- CSS animations only (fadeInUp, slideInRight, slideInLeft, fadeIn) — no framer-motion
- Inline SVGs only — no icon libraries
- Stagger classes `.stagger-1` through `.stagger-10` in `index.css`
- `text-[16px]` on inputs prevents iOS auto-zoom
- All colors use `tg-*` tokens for Telegram dark/light theme support
- `HapticFeedback` available via `window.Telegram.WebApp.HapticFeedback`

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
