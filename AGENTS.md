# AGENTS.md

> Project map for AI agents. Keep this file up-to-date as the project evolves.

## Project Overview
AI-powered Telegram nutrition bot with sales funnel and Mini App CRM for fitness trainer client management. Two services (bot, CRM) share a single PostgreSQL database.

## Tech Stack
- **Bot:** Python 3.11+ / aiogram 3.x + OpenRouter (Gemini 3 Flash)
- **CRM:** TypeScript modular monolith — Express (server) + React 18 + Vite + Tailwind + shadcn/ui (client) + shared types
- **Database:** PostgreSQL (Supabase)
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
│   ├── tests/                  # pytest tests (340+)
│   └── scripts/                # Utility scripts (trigger_funnel)
├── crm/                        # CRM modular monolith (TypeScript)
│   ├── shared/                 # Shared types and constants
│   │   ├── types.ts            # User, ChatMessage, UserEvent, Stats, UserFilters
│   │   └── constants.ts        # goalLabels, activityLabels, eventButtonLabels
│   ├── server/                 # Express API
│   │   ├── app.ts              # Express app (routes, middleware, static)
│   │   ├── index.ts            # Entry point: app.listen()
│   │   ├── auth.ts             # Telegram initData auth middleware
│   │   ├── db.ts               # PostgreSQL pool (SSL)
│   │   ├── modules/
│   │   │   ├── users/routes.ts # GET /api/users, /recent, /:chatId
│   │   │   ├── chat/routes.ts  # GET /api/chat/:sessionId
│   │   │   ├── stats/routes.ts # GET /api/stats
│   │   │   └── events/routes.ts# GET /api/events/:chatId
│   │   └── __tests__/          # vitest + supertest tests
│   ├── client/                 # React Mini App CRM
│   │   ├── App.tsx             # Main app (list/detail views, clients/recent tabs)
│   │   ├── components/         # UI components
│   │   │   ├── ui/             # shadcn/ui base components
│   │   │   ├── UserList.tsx    # Client list with filters
│   │   │   ├── UserDetail.tsx  # Full client profile + chat + events
│   │   │   └── ...
│   │   ├── hooks/useApi.ts     # API hooks (re-exports shared types/constants)
│   │   └── lib/utils.ts        # cn() utility (clsx + tailwind-merge)
│   ├── package.json            # Unified deps
│   ├── tsconfig.json           # Client tsconfig
│   ├── tsconfig.server.json    # Server tsconfig
│   ├── vite.config.ts          # Vite (client build + dev proxy)
│   ├── tailwind.config.js      # ESM config (never use require!)
│   └── railway.json            # Railway deployment
├── db/                         # Database schema (shared contract)
│   └── schema.sql              # CREATE TABLE + triggers (pg_dump)
├── docs/                       # Documentation
│   └── bot-documentation.md    # Bot feature documentation
├── .ai-factory/                # AI Factory context
│   ├── DESCRIPTION.md          # Project specification
│   └── ARCHITECTURE.md         # Modular Monolith architecture guidelines
├── CLAUDE.md                   # Agent instructions
├── AGENTS.md                   # This file
└── ISSUES.md                   # Known issues and fix plan
```

## Key Entry Points
| File | Purpose |
|------|---------|
| `bot/src/main.py` | Bot entry: starts polling, scheduler, webhook server |
| `bot/src/bot.py` | Creates Bot + Dispatcher, registers routers/middlewares |
| `crm/server/index.ts` | CRM server startup |
| `crm/server/app.ts` | Express app configuration (import for testing) |
| `crm/client/App.tsx` | React SPA root component |
| `crm/shared/types.ts` | Shared TypeScript interfaces (single source of truth) |
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
| `GET /api/users/recent` | Recent users (days, limit) |
| `GET /api/users/:chatId` | User detail |
| `GET /api/stats` | Aggregated stats |
| `GET /api/chat/:sessionId` | Chat history |
| `GET /api/events/:chatId` | User events |

## Documentation
| Document | Path | Description |
|----------|------|-------------|
| Agent Instructions | CLAUDE.md | Build commands, architecture, patterns |
| Project Spec | .ai-factory/DESCRIPTION.md | Tech stack and feature spec |
| Architecture | .ai-factory/ARCHITECTURE.md | Modular Monolith guidelines |
| Bot Docs | docs/bot-documentation.md | Bot features and messages |
| DB Schema | db/schema.sql | Database tables and triggers |
| Known Issues | ISSUES.md | Security/quality issues and fix plan |
