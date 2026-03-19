# Plan: Миграция на Modular Monolith

- **Branch:** `refactor/modular-monolith`
- **Created:** 2026-03-18
- **Type:** refactor
- **Architecture:** Modular Monolith (`.ai-factory/ARCHITECTURE.md`)

## Settings

- **Testing:** Yes — адаптировать существующие тесты под новую структуру
- **Logging:** Verbose — DEBUG логи при старте, загрузке модулей
- **Docs:** Yes — обновить CLAUDE.md, AGENTS.md, DESCRIPTION.md, ISSUES.md

## Summary

Объединить `backend/` и `frontend/` в единый `crm/` проект (server + client + shared types). Очистить legacy n8n и мусор. Bot остаётся отдельным Python-сервисом без изменений.

## Tasks

### Phase 1: Очистка (Task #1)
- [x] Удалить bot/32164/, bot/source/, bot/build/, bot/src/vanya_bot.egg-info/
- [x] Удалить docs/issues.md, docs/testing-report.md
- [x] Удалить n8n-mcp блок из .mcp.json
- [x] Убрать n8n/ из AGENTS.md

### Phase 2: Shared types (Task #2) ← blocked by #1
- [x] Создать crm/shared/types.ts (User, ChatMessage, UserEvent, Stats, UserFilters)
- [x] Создать crm/shared/constants.ts (goalLabels, activityLabels, eventButtonLabels)
- [x] Создать структуру директорий crm/server/modules/*, crm/client/*

### Phase 3: Backend → crm/server (Task #3) ← blocked by #2
- [x] Перенести app.ts, index.ts, db.ts
- [x] Разнести routes → modules/*/routes.ts
- [x] Убрать hardcoded DB fallback из db.ts
- [x] Обновить импорты на shared/types

### Phase 4: Frontend → crm/client (Task #4) ← blocked by #2
- [x] Перенести все компоненты, hooks, lib, CSS
- [x] Рефакторить useApi.ts — убрать типы и константы, импортировать из shared/
- [x] Обновить все import paths

### Phase 5: Build pipeline (Task #5) ← blocked by #3, #4
- [x] Создать единый crm/package.json (объединить deps)
- [x] Настроить tsconfig.json с project references
- [x] Настроить vite.config.ts (alias, proxy, output)
- [x] Перенести tailwind.config.js, postcss.config.js
- [x] Создать crm/railway.json
- [x] Удалить корневой package.json

### Phase 6: Тесты (Task #6) ← blocked by #5
- [x] Перенести __tests__ → crm/server/__tests__/
- [x] Обновить import paths и mock paths
- [x] Настроить vitest.config.ts
- [x] Запустить и убедиться что все проходят (17/17)
- [x] Проверить что bot тесты не сломались (340/340)

### Phase 7: БД и cleanup (Task #7) ← blocked by #6
- [x] pg_dump --schema-only → db/schema.sql
- [x] Удалить backend/ и frontend/ директории
- [x] Обновить .gitignore

### Phase 8: Документация (Task #8) ← blocked by #7
- [x] Обновить CLAUDE.md
- [x] Обновить AGENTS.md
- [x] Обновить DESCRIPTION.md
- [x] Обновить ISSUES.md
- [x] Проверить docs/bot-documentation.md

## Commit Plan

| Checkpoint | Tasks | Commit message |
|------------|-------|----------------|
| 1 | #1 | `chore: clean up junk files and remove n8n legacy` |
| 2 | #2, #3, #4 | `refactor: migrate backend and frontend into crm/ modular monolith` |
| 3 | #5, #6 | `refactor: configure unified build pipeline and adapt tests` |
| 4 | #7, #8 | `chore: export DB schema, remove old dirs, update docs` |

## Dependency Graph

```
#1 Cleanup
 └→ #2 Shared types
     ├→ #3 Backend → crm/server ─┐
     └→ #4 Frontend → crm/client ┘
                                  └→ #5 Build pipeline
                                      └→ #6 Tests
                                          └→ #7 DB + cleanup
                                              └→ #8 Docs
```
