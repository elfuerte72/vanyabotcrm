# Plan: Улучшение отображения чата и воронки в CRM

- **Branch:** `feature/crm-chat-display`
- **Created:** 2026-04-10
- **Type:** enhancement

## Settings

- **Testing:** Yes
- **Logging:** Standard
- **Docs:** No

## Summary

CRM отображает историю диалога с некорректными/непонятными лейблами:
1. Сырые коды воронки ("wakeup_sent", "stage_0_zone_ask") вместо описаний
2. Сырые callback кнопок ("zone_belly") вместо "Выбрал зону: Низ живота"
3. Прогресс-бар воронки жёстко показывает "из 6" вместо реального количества этапов
4. AI-сообщения (КБЖУ, рацион) могут быть неполными или плохо отформатированными

## Tasks

### Phase 1: Данные и лейблы

#### Task 1: Добавить недостающие лейблы кнопок и воронки
**Files:** `crm/shared/constants.ts`

- [x] Добавить в `eventButtonLabels`: zone_belly, zone_thighs, zone_arms, zone_glutes
- [x] Расширить `funnelStageLabels` с описательными названиями для всех event_data
- [x] Добавить `funnelVariantLabels`: belly→"Низ живота", thighs→"Ушки на бёдрах", etc.
- [x] Добавить `getMaxFunnelStage`: функция для определения max этапа по языку и варианту

### Phase 2: UI компоненты

#### Task 2: Улучшить FunnelCard
**Files:** `crm/client/components/ChatHistory.tsx`

- [x] Заменить ручной `replace()` на lookup из `funnelStageLabels`
- [x] Показывать полный текст сообщения воронки (лимит увеличен до 300)
- [x] Toggle свернуть/развернуть для длинных текстов

#### Task 3: Исправить прогресс-бар воронки
**Files:** `crm/client/components/UserDetail.tsx`

- [x] Определять max этапов по `user.language` и `user.funnel_variant`
- [x] Показывать `funnel_variant` в заголовке (если есть)
- [x] Динамическое количество сегментов прогресс-бара

#### Task 4: Улучшить отображение AI-сообщений
**Files:** `crm/client/components/ChatHistory.tsx`

- [x] Добавить свернуть/развернуть для длинных AI-сообщений (ChatMessageCard)
- [x] Обработка HTML-тегов через stripHtml

### Phase 3: Тесты

#### Task 5: Написать тесты
**Files:** `crm/server/__tests__/constants.test.ts`

- [x] Тест покрытия всех known event_data в eventButtonLabels (31 ключ)
- [x] Тест покрытия всех funnel stage event_data в funnelStageLabels (15 ключей)
- [x] Тест funnelVariantLabels (4 зоны)
- [x] Тест getMaxFunnelStage по языку и варианту (5 кейсов)

## Commit Plan

- **Commit 1** (после Tasks 1-2): `feat(crm): add funnel stage descriptions and button labels`
- **Commit 2** (после Tasks 3-4): `feat(crm): improve funnel progress bar and AI message display`
- **Commit 3** (после Task 5): `test(crm): add tests for funnel labels and display logic`
