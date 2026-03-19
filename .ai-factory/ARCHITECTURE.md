# Architecture: Modular Monolith

## Overview
Проект состоит из двух независимых сервисов: **Bot** (Python/aiogram) и **CRM** (TypeScript/Express+React). Каждый деплоится на Railway отдельно. Внутри CRM используется модульный монолит — единый TypeScript-проект с чёткими границами модулей (users, chat, stats, events) и общими типами между server и client.

Этот паттерн выбран потому что: маленькая команда (1-2 разработчика), CRM — это read-heavy приложение с простой логикой, а объединение frontend и backend в один проект устраняет дублирование типов и упрощает сборку.

## Decision Rationale
- **Project type:** Telegram бот + Mini App CRM
- **Tech stack:** Python/aiogram (bot), TypeScript/Express+React (CRM)
- **Key factor:** Backend CRM слишком тонкий для отдельного проекта — 4 read-only эндпоинта без бизнес-логики. Общие типы между server и client устраняют рассинхронизацию.

## Folder Structure

### Целевая структура
```
monitoringsql/
├── bot/                        # Python — отдельный сервис (aiogram)
│   ├── src/
│   │   ├── handlers/           # Telegram event handlers
│   │   │   ├── start.py
│   │   │   ├── message.py
│   │   │   ├── callbacks.py
│   │   │   └── payment.py
│   │   ├── services/           # Бизнес-логика (AI, калькулятор, форматтер)
│   │   ├── funnel/             # Воронка продаж (messages, sender, scheduler)
│   │   ├── i18n/               # Локализация (ru, en, ar)
│   │   ├── db/                 # asyncpg pool + SQL queries
│   │   ├── models/             # Dataclasses
│   │   ├── middlewares/        # Logging, subscription check, user loading
│   │   ├── bot.py              # Bot + Dispatcher factory
│   │   └── main.py             # Entry point
│   ├── config/                 # Pydantic Settings + media.yaml
│   ├── tests/
│   ├── scripts/
│   ├── pyproject.toml
│   └── requirements.txt
│
├── crm/                        # TypeScript — единый CRM (server + client)
│   ├── server/                 # Express API
│   │   ├── modules/
│   │   │   ├── users/
│   │   │   │   └── routes.ts   # GET /api/users, /api/users/:chatId
│   │   │   ├── chat/
│   │   │   │   └── routes.ts   # GET /api/chat/:sessionId
│   │   │   ├── stats/
│   │   │   │   └── routes.ts   # GET /api/stats
│   │   │   └── events/
│   │   │       └── routes.ts   # GET /api/events/:chatId
│   │   ├── db.ts               # PostgreSQL pool
│   │   ├── auth.ts             # Telegram initData middleware
│   │   ├── app.ts              # Express app (routes, middleware, static)
│   │   └── index.ts            # Entry point: app.listen()
│   ├── client/                 # React SPA (Telegram Mini App)
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui base components
│   │   │   ├── UserList.tsx
│   │   │   ├── UserDetail.tsx
│   │   │   └── ...
│   │   ├── hooks/
│   │   │   └── useApi.ts       # API hooks (используют shared/types)
│   │   ├── lib/
│   │   │   └── utils.ts        # cn() helper
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── shared/                 # Общий код между server и client
│   │   ├── types.ts            # User, ChatMessage, Event, Stats интерфейсы
│   │   └── constants.ts        # goalLabels, activityLabels, eventButtonLabels
│   ├── package.json            # Один для всего CRM
│   ├── tsconfig.json           # Общий tsconfig с project references
│   ├── vite.config.ts          # Vite (client build + dev proxy)
│   └── vitest.config.ts        # Тесты server
│
├── db/                         # Схема БД (shared контракт)
│   └── schema.sql              # CREATE TABLE statements + triggers
│
├── CLAUDE.md
├── AGENTS.md
├── ISSUES.md
└── .ai-factory/
```

### Что меняется относительно текущей структуры
| Было | Стало |
|------|-------|
| `backend/` + `frontend/` + корневой `package.json` | `crm/` (единый проект) |
| Типы дублировались в `useApi.ts` и routes | `crm/shared/types.ts` — единый источник |
| Константы в `hooks/useApi.ts` | `crm/shared/constants.ts` |
| `backend/src/routes/*.ts` | `crm/server/modules/*/routes.ts` |
| Нет схемы БД в коде | `db/schema.sql` |
| `bot/32164/`, `bot/source/`, `bot/build/` | Удалены (мусор) |
| `n8n/`, `docs/issues.md` | Удалены (legacy) |

## Dependency Rules

### CRM (TypeScript)
- ✅ `server/modules/*` → `server/db.ts`, `shared/*`
- ✅ `client/components/*` → `client/hooks/*`, `client/lib/*`, `shared/*`
- ✅ `client/hooks/*` → `shared/types.ts`
- ❌ `server/` → `client/` (сервер не импортирует клиентский код)
- ❌ `client/` → `server/` (клиент не импортирует серверный код)
- ❌ `shared/` → `server/` или `client/` (shared не знает о конкретных слоях)
- ❌ Модуль → внутренности другого модуля (`users/` не лезет в `chat/`)

### Bot (Python)
- ✅ `handlers/` → `services/`, `db/`, `i18n/`, `models/`
- ✅ `services/` → `db/`, `models/`
- ✅ `funnel/` → `db/`, `i18n/`
- ❌ `db/` → `handlers/`, `services/`
- ❌ `models/` → что-либо кроме стандартной библиотеки

### Cross-service
- ❌ Bot и CRM не импортируют код друг друга
- ✅ Единственный контракт — схема БД (`db/schema.sql`)

## Module Communication

### Внутри CRM
```
User action → Component → useApi hook → fetch(/api/*) → Express route → db.query() → PostgreSQL
                ↑                                              ↑
            shared/types.ts                              shared/types.ts
```
Server и client используют одни и те же TypeScript-интерфейсы из `shared/`.

### Между сервисами
```
Bot writes → PostgreSQL ← CRM reads → Frontend displays
```
Нет прямого взаимодействия. БД — единственный shared state.

## Key Principles

1. **Один проект = один деплой для CRM.** `crm/` билдится один раз: Vite собирает client → Express раздаёт static + API. Один `package.json`.

2. **Shared types — единый источник правды.** Интерфейсы `User`, `ChatMessage`, `UserEvent` определяются в `shared/types.ts` и используются и в server routes, и в client hooks. Нет дублирования.

3. **Модуль = домен.** Каждый модуль в `server/modules/` отвечает за один ресурс (users, chat, stats, events). Модуль экспортирует только свой router.

4. **Bot остаётся отдельным.** Python-сервис деплоится независимо. У него своя архитектура (layered), свой `requirements.txt`, свой Railway service.

5. **Схема БД в коде.** `db/schema.sql` — документация контракта между Bot и CRM. При изменении таблиц — обновить файл.

## Code Examples

### Shared types (единый источник)
```typescript
// crm/shared/types.ts
export interface User {
  chat_id: number;
  username: string | null;
  first_name: string;
  sex: string | null;
  age: number | null;
  weight: number | null;
  height: number | null;
  activity_level: string | null;
  goal: string | null;
  calories: number | null;
  protein: number | null;
  fats: number | null;
  carbs: number | null;
  funnel_stage: number;
  is_buyer: boolean;
  get_food: boolean;
  language: string;
}

export interface ChatMessage {
  id: number;
  session_id: string;
  message: {
    type: 'human' | 'ai';
    content: string;
  };
}

export type Goal = 'weight_loss' | 'weight_gain' | 'maintenance' | 'muscle_gain';
```

### Server module (модульный роутер)
```typescript
// crm/server/modules/users/routes.ts
import { Router } from 'express';
import { pool } from '../../db';
import type { User } from '../../../shared/types';

const router = Router();

router.get('/api/users', async (req, res) => {
  const { search, status, sort, order } = req.query;
  // ... build query
  const result = await pool.query<User>(query, params);
  res.json(result.rows);
});

export default router;
```

### Client hook (использует shared types)
```typescript
// crm/client/hooks/useApi.ts
import type { User, ChatMessage } from '../../shared/types';

export function useUsers(filters: UserFilters) {
  const params = new URLSearchParams();
  if (filters.search) params.set('search', filters.search);
  return useFetch<User[]>(`/api/users?${params}`);
}
```

### Server app (собирает модули)
```typescript
// crm/server/app.ts
import usersRouter from './modules/users/routes';
import chatRouter from './modules/chat/routes';
import statsRouter from './modules/stats/routes';
import eventsRouter from './modules/events/routes';

app.use(authMiddleware);
app.use(usersRouter);
app.use(chatRouter);
app.use(statsRouter);
app.use(eventsRouter);
```

## Anti-Patterns

- ❌ **Импорт между server и client.** `shared/` — единственный мост. Server-код не должен попадать в client bundle, client-код не нужен серверу.
- ❌ **Модуль знает о другом модуле.** `users/routes.ts` не импортирует из `chat/routes.ts`. Если нужны данные из нескольких модулей — создай отдельный составной эндпоинт.
- ❌ **Бизнес-логика в shared.** `shared/` содержит только типы и константы. Никакой логики, никаких side effects.
- ❌ **Прямой import из node_modules в shared.** Shared должен быть чистым TypeScript без зависимостей от Express, React и т.д.
- ❌ **SQL в client коде.** Клиент общается только через HTTP API, никогда напрямую с БД.

## Migration Plan (текущая → целевая)

1. **Очистка мусора:** удалить `bot/32164/`, `bot/source/`, `bot/build/`, `docs/issues.md`, legacy n8n ссылки
2. **Создать `crm/`:** объединить `backend/` и `frontend/` в единый проект
3. **Выделить `shared/`:** перенести типы и константы из `hooks/useApi.ts`
4. **Модулизировать server:** `routes/*.ts` → `modules/*/routes.ts`
5. **Настроить сборку:** один `package.json`, один Vite config с proxy, один Railway service
6. **Выгрузить схему БД:** `pg_dump --schema-only` → `db/schema.sql`
7. **Удалить корневой `package.json`** (костыль больше не нужен)
8. **Обновить Railway:** перенастроить service на `crm/`
