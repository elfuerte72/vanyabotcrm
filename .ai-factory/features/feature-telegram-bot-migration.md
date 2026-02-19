# Feature: Telegram Bot Migration (n8n → Python/aiogram)

## Summary
Перенос всей логики Telegram-бота VANYA_BOT из 9 n8n-воркфлоу в Python-приложение на aiogram 3.x с сохранением всей бизнес-логики, AI-агентов, воронки продаж и платёжных интеграций.

## Decisions
- **Language**: Python 3.11+
- **Bot framework**: aiogram 3.x (async, FSM, middleware)
- **LLM**: OpenRouter API (google/gemini-3-flash-preview)
- **Database**: PostgreSQL (existing Railway DB, asyncpg)
- **Tests**: pytest + pytest-asyncio
- **Logging**: Verbose (structlog, LOG_LEVEL configurable)
- **Media**: Config YAML file with Google Drive file IDs
- **Payments**: Tribute (RU) + Ziina (EN/AR) — webhook handlers

## Project Structure

```
bot/
├── pyproject.toml              # Dependencies & project config
├── .env.example                # Environment variables template
├── config/
│   ├── settings.py             # Pydantic settings (env vars)
│   └── media.yaml              # Google Drive file IDs & URLs
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point: bot + dispatcher setup
│   ├── bot.py                  # Bot & dispatcher factory
│   ├── db/
│   │   ├── __init__.py
│   │   ├── pool.py             # asyncpg connection pool
│   │   └── queries.py          # All SQL queries (typed)
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py            # /start command
│   │   ├── message.py          # Text & voice message handler
│   │   ├── callbacks.py        # Inline button callbacks (buy_now, show_info, etc.)
│   │   └── payment.py          # Ziina webhook handler
│   ├── middlewares/
│   │   ├── __init__.py
│   │   ├── subscription.py     # Check @ivanfit_health membership
│   │   ├── user_data.py        # Load user from DB, inject into handler
│   │   └── logging.py          # Request/response logging
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_agent.py         # AGENT MAIN: nutrition consultant conversation
│   │   ├── ai_food.py          # AGENT FOOD: meal plan generation
│   │   ├── calculator.py       # Mifflin-St Jeor KBJU calculator
│   │   ├── formatter.py        # AI response → Telegram HTML formatter
│   │   ├── media.py            # Google Drive file download & send
│   │   └── language.py         # Language detection (regex-based)
│   ├── funnel/
│   │   ├── __init__.py
│   │   ├── scheduler.py        # Daily cron job (apscheduler)
│   │   ├── messages.py         # Day 1-5 messages (all languages)
│   │   └── sender.py           # Batch send funnel messages
│   ├── i18n/
│   │   ├── __init__.py
│   │   ├── ru.py               # Russian strings
│   │   ├── en.py               # English strings
│   │   └── ar.py               # Arabic strings
│   └── models/
│       ├── __init__.py
│       └── user.py             # User dataclass / Pydantic model
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Fixtures (mock DB, bot, etc.)
│   ├── test_calculator.py      # KBJU calculation tests
│   ├── test_language.py        # Language detection tests
│   ├── test_formatter.py       # HTML formatting tests
│   ├── test_funnel.py          # Funnel stage logic tests
│   └── test_callbacks.py       # Callback handler tests
└── README.md
```

## Implementation Tasks

### Task 1: Project scaffolding
- Create `bot/` directory with structure above
- `pyproject.toml` with dependencies: aiogram>=3.15, asyncpg, httpx, pydantic-settings, structlog, apscheduler, pyyaml, pytest, pytest-asyncio
- `.env.example` with all required vars
- `config/settings.py` — Pydantic BaseSettings
- `config/media.yaml` — Google Drive IDs from n8n workflows

### Task 2: Database layer
- `db/pool.py` — asyncpg pool with SSL (`ssl=require`)
- `db/queries.py` — all SQL queries as typed async functions:
  - `get_user(chat_id)` → User | None
  - `save_user_data(chat_id, sex, weight, height, age, activity, goal, allergies, excluded, calories, protein, fats, carbs, language)`
  - `mark_as_buyer(chat_id)`
  - `set_food_received(chat_id)` — set get_food=TRUE, funnel_stage=0
  - `get_funnel_targets()` — non-buyers with funnel_stage 0-4
  - `update_funnel_stage(chat_id)` — increment funnel_stage

### Task 3: Core services
- `services/language.py` — regex detection (Arabic → Russian → English)
- `services/calculator.py` — Mifflin-St Jeor formula (exact copy of n8n Code node logic)
- `services/formatter.py` — Markdown→HTML, JSON extraction from AI output, meal plan HTML rendering
- `services/media.py` — Google Drive download via httpx + send via Telegram API

### Task 4: AI Agents (OpenRouter)
- `services/ai_agent.py` — AGENT MAIN:
  - System prompt (exact copy from n8n)
  - Chat memory via `n8n_chat_histories` table (same format for backward compat)
  - Conversation mode → returns text_response
  - Finished mode → returns JSON with user data
  - Voice support: receive voice → download → OpenAI Whisper → text → agent
- `services/ai_food.py` — AGENT FOOD:
  - System prompt with injected KBJU targets
  - JSON output → validation (calorie tolerance 10%) → HTML formatting

### Task 5: Handlers
- `handlers/start.py` — /start command handler
- `handlers/message.py`:
  - Load user from DB
  - If get_food=True → "can't calculate twice"
  - Check subscription → if no → "subscribe to channel"
  - Route: text → AI agent, voice → transcribe → AI agent
  - Process AI response (conversation vs generate)
  - If generate → calculator → save to DB → AGENT FOOD → send menu
- `handlers/callbacks.py`:
  - `buy_now` → mark buyer + send payment link (by language: Tribute/Ziina)
  - `show_info` → download video from GDrive → send
  - `show_results` → random photo from GDrive → send
  - `check_suitability` → download suitability video → send
  - `remind_later` → acknowledgment message
  - `none` → motivational message + channel link
  - `video_workout` → offer to buy

### Task 6: Funnel system
- `funnel/messages.py` — all Day 1-5 messages for RU/EN/AR (exact copy from n8n)
- `funnel/scheduler.py` — APScheduler cron job (daily)
- `funnel/sender.py` — batch processing: get targets → route by language → send message → update stage

### Task 7: i18n & Localization
- Extract all static strings from n8n into `i18n/ru.py`, `i18n/en.py`, `i18n/ar.py`
- Callback messages, error messages, subscription prompts
- Payment URLs per language

### Task 8: Payment webhook
- `handlers/payment.py` — Ziina webhook HTTP endpoint (aiohttp or separate)
- Verify payment → update is_buyer → send content to user

### Task 9: Middlewares
- `middlewares/subscription.py` — getChatMember check for @ivanfit_health
- `middlewares/user_data.py` — load user from DB, detect language, inject into context
- `middlewares/logging.py` — structured logging for all events

### Task 10: Tests
- `test_calculator.py` — BMR, TDEE, macros for various inputs
- `test_language.py` — Arabic, Russian, English, mixed text detection
- `test_formatter.py` — Markdown→HTML, JSON extraction, meal plan rendering
- `test_funnel.py` — stage transitions, message selection
- `test_callbacks.py` — callback routing logic

### Task 11: Entry point & wiring
- `main.py` — setup bot, dispatcher, register handlers, start polling
- `bot.py` — factory function for Bot + Dispatcher with all middleware/handlers

## Key Business Logic to Preserve

### KBJU Calculator (Mifflin-St Jeor)
```
Male:   BMR = 10*weight + 6.25*height - 5*age + 5
Female: BMR = 10*weight + 6.25*height - 5*age - 161

Activity multipliers: sedentary=1.2, light=1.375, moderate=1.55, high=1.725, extreme=1.9

Goals: weight_loss=-15%, muscle_gain=+10%, maintenance=0%

Protein: 1.3-1.5 g/kg (weight_loss/muscle_gain: 1.5, maintenance: 1.4)
Fat: 1.0 g/kg
Carbs: (calories - protein*4 - fat*9) / 4
```

### Funnel Stages
```
0 → Day 1 (free workout video)
1 → video_workout response (offer to buy)
2 → Day 2 (social proof)
3 → Day 3 (pain → solution)
4 → Day 4 (price comparison)
5 → Day 5 (soft deadline)
```

### Subscription Check
- Channel: @ivanfit_health (chat_id: -1002504147240)
- Allowed statuses: member, administrator, creator

### Payment Links
- RU: `https://t.me/tribute/app?startapp=pnvi`
- EN/AR: Ziina webhook flow

### Google Drive Media IDs (from n8n)
- Info video: `1QxlXwm-nQ6NLjmn2H1RMrGRqjEnPGfTG`
- Suitability video: `1fMoKSPu6KX8_B9pal8w3FVxi-T2Nj4L3`
- Result photos: `192D7VKnBQAhRxl2tPbkm180ryvK_JnnM`, `1shlC_81AL_zPFwG8APJtrcudA8afhbJY`, `1TawBgD-c4p7SaW2DbGUNyh16h9rA54be`
- Workout video: `1NOzdV9ajZSFNbjnhE7Mhj44LEpvhjp06`
