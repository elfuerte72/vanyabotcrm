# Project: MonitoringSQL (VanyaBot + CRM)

## Overview
AI-powered Telegram nutrition bot with sales funnel and Mini App CRM for fitness trainer client management. Two services (bot, CRM) share a single PostgreSQL database.

## Core Features
- AI nutrition consultant via Telegram (collects user data, calculates KBJU via Harris-Benedict, generates meal plans)
- Multi-language support: RU, EN, AR
- Sales funnel system: RU (13 stages with zone branching), EN/AR (11 stages with upsells)
- Telegram Mini App CRM for client management (user list, detail view, chat history, events)
- Payment integration (Tribute for RU, Ziina for EN/AR with webhook verification)
- Scheduled funnel message delivery via APScheduler (every 15 min)

## Tech Stack
- **Bot Language:** Python 3.11+
- **Bot Framework:** aiogram 3.x
- **Bot AI:** OpenRouter (Gemini 3 Flash)
- **Bot Async DB:** asyncpg
- **Bot Scheduler:** APScheduler 3.x
- **CRM Language:** TypeScript
- **CRM Server:** Express 4.x
- **CRM Client:** React 18 + Vite 5 + Tailwind CSS 3 + shadcn/ui
- **CRM Testing:** Vitest + Supertest
- **Database:** PostgreSQL (Supabase, project: dnzwpdcvrpfiipjwpxux)
- **Deployment:** Railway (Nixpacks)
- **Automation:** n8n (via MCP)

## Architecture Notes
- Two independent services share one PostgreSQL database (shared contract in `db/schema.sql`)
- CRM is a modular monolith: Express API + React SPA in a single TypeScript project with shared types
- Bot uses factory pattern for Bot/Dispatcher creation with lazy config initialization
- Funnel messages are zone-specific (belly, thighs, arms, glutes) for RU; universal for EN/AR
- Real-time DB notifications via PostgreSQL NOTIFY triggers on `users_nutrition`

## Non-Functional Requirements
- Logging: structlog (bot), pino (CRM), configurable via LOG_LEVEL
- Error handling: structured error responses in CRM (zod validation)
- Security: Telegram initData auth, helmet, rate limiting (100 req/min), Ziina webhook signature validation
- Rate limits: Telegram API — 25 messages per batch with 1-sec delay
- SSL: enabled for all database connections (Supabase)

## Architecture
See `.ai-factory/ARCHITECTURE.md` for detailed architecture guidelines.
Pattern: Modular Monolith (Dual-Service)
