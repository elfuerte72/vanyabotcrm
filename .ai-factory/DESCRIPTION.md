# Project: VanyaBot CRM

## Overview
AI-powered Telegram bot for a fitness trainer that acts as a nutrition consultant. Collects user data through conversational AI (Gemini 3 Flash via OpenRouter), calculates KBJU (calories, protein, fats, carbs) using Mifflin-St Jeor formula, generates personalized meal plans, and runs a 5-day automated sales funnel. Includes a Telegram Mini App CRM for the trainer to view all clients, track buyer/lead status, and monitor the sales pipeline.

## Core Features
- AI nutrition consultant via Telegram (conversational data collection)
- KBJU calculation (Mifflin-St Jeor) with personalized meal plan generation
- 5-day automated sales funnel (APScheduler, daily at 23:00 UTC)
- Telegram channel subscription check (Russian-speaking users only, `language = ru`)
- Multi-language support: Russian, English, Arabic
- Payment integration (Ziina via webhook on port 8080)
- Mini App CRM: client list, buyer/lead filtering, chat history, user events timeline
- User events tracking (button clicks, bot responses, funnel events)

## Tech Stack
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui (Telegram Mini App)
- **Backend:** Express + TypeScript (REST API for Mini App CRM)
- **Bot:** Python 3.11+ / aiogram 3.x (Telegram bot with AI agents)
- **AI:** OpenRouter API (google/gemini-3-flash-preview) for conversation and meal plan generation
- **Database:** PostgreSQL (Railway, shared across all services)
- **Auth:** Telegram `initData` validation via `@telegram-apps/init-data-node`
- **Scheduler:** APScheduler (funnel cron job)
- **Payments:** Ziina (webhook-based)
- **Deployment:** Railway (Nixpacks builder)

## Architecture Notes
Three services share a single PostgreSQL database on Railway:
1. **Bot** (Python/aiogram) — handles Telegram interactions, AI conversations, KBJU calculation, meal plan generation, funnel automation
2. **Backend** (Express/TypeScript) — REST API serving the Mini App CRM with user data, chat history, events, and stats
3. **Frontend** (React/Vite) — Telegram Mini App providing trainer with client management interface

The bot writes user data and chat history; the CRM reads it. Chat history uses `n8n_chat_histories` table (backward-compatible with legacy n8n format).

## Architecture
See `.ai-factory/ARCHITECTURE.md` for detailed architecture guidelines.
Pattern: Layered Architecture

## Non-Functional Requirements
- Logging: Configurable via `LOG_LEVEL` (default: DEBUG) with structlog
- Error handling: Structured error responses in API, graceful bot error handling
- Security: Telegram initData auth (1hr expiry), SSL database connections, subscription gating for RU users
- Testing: pytest for bot (58+ tests), vitest + supertest for backend
- i18n: Three languages (ru, en, ar) with dedicated string modules
