# AGENTS.md

> Project map for AI agents. Keep this file up-to-date as the project evolves.

## Project Overview
AI-powered Telegram nutrition bot with sales funnel and Mini App CRM for fitness trainer client management. Three services (bot, backend, frontend) share a single PostgreSQL database.

## Tech Stack
- **Bot:** Python 3.11+ / aiogram 3.x + OpenRouter (Gemini 3 Flash)
- **Backend:** Express + TypeScript
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Database:** PostgreSQL (Railway)
- **Deployment:** Railway (Nixpacks)

## Project Structure
```
monitoringsql/
├── bot/                        # Telegram bot (Python/aiogram)
│   ├── src/
│   │   ├── main.py             # Entry: polling + scheduler + webhook
│   │   ├── bot.py              # Bot/Dispatcher factory
│   │   ├── handlers/           # Telegram handlers (start, message, callbacks, payment)
│   │   ├── middlewares/        # Logging → subscription check → user data loading
│   │   ├── services/           # AI agents, calculator, formatter, language, media
│   │   ├── funnel/             # Sales funnel: messages, sender, scheduler
│   │   ├── i18n/               # Localized strings (ru, en, ar)
│   │   ├── db/                 # asyncpg pool + SQL queries
│   │   └── models/             # User dataclass
│   ├── config/                 # Pydantic Settings + media.yaml
│   ├── tests/                  # pytest tests (58+)
│   └── scripts/                # Utility scripts (trigger_funnel)
├── backend/                    # Express API for Mini App CRM
│   ├── src/
│   │   ├── index.ts            # Server startup (app.listen)
│   │   ├── app.ts              # Express app (routes, middleware, static)
│   │   ├── db.ts               # PostgreSQL pool (SSL)
│   │   ├── auth.ts             # Telegram initData auth middleware
│   │   └── routes/             # API routes (users, chat, stats, events)
│   └── src/__tests__/          # vitest + supertest tests
├── frontend/                   # React Mini App CRM
│   ├── src/
│   │   ├── App.tsx             # Main app (list/detail views, clients/recent tabs)
│   │   ├── components/         # UI components
│   │   │   ├── ui/             # shadcn/ui base components
│   │   │   ├── UserList.tsx    # Client list with filters
│   │   │   ├── UserDetail.tsx  # Full client profile + chat + events
│   │   │   └── ...
│   │   ├── hooks/useApi.ts     # All API hooks, types, shared constants
│   │   └── lib/utils.ts        # cn() utility (clsx + tailwind-merge)
│   ├── tailwind.config.js      # ESM config (never use require!)
│   └── index.html              # SPA entry
├── n8n/                        # Legacy n8n workflow JSONs (reference only)
├── docs/                       # Documentation
│   └── bot-documentation.md    # Bot feature documentation
├── .ai-factory/                # AI Factory context
│   ├── DESCRIPTION.md          # Project specification
│   └── PLAN.md                 # Current implementation plan
├── CLAUDE.md                   # Agent instructions
└── AGENTS.md                   # This file
```

## Key Entry Points
| File | Purpose |
|------|---------|
| `bot/src/main.py` | Bot entry: starts polling, scheduler, webhook server |
| `bot/src/bot.py` | Creates Bot + Dispatcher, registers routers/middlewares |
| `backend/src/index.ts` | Backend server startup |
| `backend/src/app.ts` | Express app configuration (import for testing) |
| `frontend/src/App.tsx` | React SPA root component |
| `bot/config/settings.py` | Bot configuration (Pydantic Settings, lazy init) |

## Key Database Tables
| Table | Purpose |
|-------|---------|
| `users_nutrition` | User profiles, KBJU data, funnel stage, buyer status |
| `n8n_chat_histories` | Chat messages (JSONB, legacy n8n format) |
| `user_events` | Button clicks, funnel events, interaction timeline |

## API Endpoints
| Endpoint | Purpose |
|----------|---------|
| `GET /api/users` | List users (search, filter, sort) |
| `GET /api/users/:chatId` | User detail |
| `GET /api/stats` | Aggregated stats |
| `GET /api/chat/:sessionId` | Chat history |
| `GET /api/events/:chatId` | User events |

## Documentation
| Document | Path | Description |
|----------|------|-------------|
| Agent Instructions | CLAUDE.md | Build commands, architecture, patterns |
| Project Spec | .ai-factory/DESCRIPTION.md | Tech stack and feature spec |
| Bot Docs | docs/bot-documentation.md | Bot features and messages |

## AI Context Files
| File | Purpose |
|------|---------|
| AGENTS.md | This file — project structure map |
| .ai-factory/DESCRIPTION.md | Project specification and tech stack |
| .ai-factory/ARCHITECTURE.md | Architecture decisions and guidelines |
| CLAUDE.md | Agent instructions and preferences |
