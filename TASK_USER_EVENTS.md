# ТЗ: Отслеживание нажатий кнопок пользователей в CRM

## Проблема

Сейчас в CRM видна только переписка клиента с AI-агентом (таблица `n8n_chat_histories`). Нажатия inline-кнопок (callback_query) обрабатываются отдельной веткой в MAIN v2 и **никуда не логируются**. Мы не видим, какие кнопки нажимал пользователь и когда.

## Цель

Отображать в CRM полную картину взаимодействия пользователя с ботом: сообщения чата + нажатия кнопок + события воронки — в виде единой timeline.

---

## Текущая архитектура n8n (что есть)

### MAIN v2 (workflow `cXhW3Mu9WdRnk0Fe`)

Главный Telegram Trigger, слушает `message` и `callback_query`.

```
Telegram Trigger
  │
  If2: callback_query exists?
  ├── YES → get language (Postgres) → callback router (Switch по language)
  │     ├── ru → Call callback_ru (workflow 2GGB7l9opUfOHgpo)
  │     ├── en → Call callback_en (workflow B6QkQPsiMrigBfY4)
  │     └── ar → Call callback_ar (workflow jlwgyCM5RPUxTBhG)
  │
  └── NO (message) → get db user → ... → AGENT MAIN → ...
```

### callback_ru (workflow `2GGB7l9opUfOHgpo`)

Входные параметры: `callback_query_data`, `callback_query_message_chat_id`, `callback_query_id`

Router по `callback_query_data`:
| Значение | Действие |
|----------|----------|
| `buy_now` | Mark as Buyer (UPDATE is_buyer=TRUE) → ссылка на оплату |
| `show_info` | Отправка видео с информацией |
| `show_results` | Рандомное фото результатов |
| `remind_later` | Ответ "ты на верном пути" |
| `check_suitability` | Видео "подходит ли тебе" |
| `none` | Отказное сообщение |

### callback_en (workflow `B6QkQPsiMrigBfY4`)

Входные параметры: `callback_query_data`, `callback_query_message_chat_id`, `callback_query_id`, `callback_query_from_id`

Router по `callback_query_data`:
| Значение | Действие |
|----------|----------|
| `buy_now` | Ссылка на оплату (Tribute) |
| `nutrition_en` | Сообщение о питании |
| `cardio_en` | Сообщение о кардио |
| `different` | Сообщение "different" |
| `beginner` | Сообщение для начинающих |
| `price` | Информация о цене |
| `help` | Помощь |
| `coaching` | Информация о коучинге |
| `gym` | Информация о тренажёрном зале |
| `access` | Доступ |
| `upgrade_79` | Создание заказа Ziina (79 AED), upsert id_ziina/type_ziina |
| `upgrade_99` | Создание заказа Ziina (99 AED), upsert id_ziina/type_ziina |

### callback_ar (workflow `jlwgyCM5RPUxTBhG`)

Аналогичная структура для арабского языка.

### days router (workflow `jno4qmE3iKt89y5d`)

Schedule Trigger (раз в сутки) → выбирает пользователей с `is_buyer=FALSE AND funnel_stage 0..4` → Switch по language → вызывает DAYS_ru/en/ar.

### DAYS_ru/en/ar

Получают список пользователей → Loop → Check Stage (Switch по funnel_stage) → Send Day 1..5 → Update Stage (funnel_stage + 1).

---

## План реализации

### 1. Новая таблица `user_events`

```sql
CREATE TABLE user_events (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data VARCHAR(255) NOT NULL,
    language VARCHAR(10),
    workflow_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_events_chat_id ON user_events(chat_id);
CREATE INDEX idx_user_events_created_at ON user_events(created_at);
```

**Поля:**
- `chat_id` — Telegram ID пользователя
- `event_type` — тип события: `button_click`, `funnel_message`, `payment_link`
- `event_data` — значение callback_query_data (`buy_now`, `show_info`, ...) или `day_1`..`day_5`
- `language` — язык пользователя (`ru`, `en`, `ar`)
- `workflow_name` — имя workflow для дебага (`callback_ru`, `DAYS_en`, ...)
- `created_at` — время события

**Почему отдельная таблица:**
- `n8n_chat_histories` содержит JSONB с форматом `{type, content}` — кнопки туда не вписываются
- Отдельная таблица позволяет фильтровать, агрегировать, строить аналитику
- Не ломает существующий парсинг чата

### 2. Изменения в n8n workflow-ах

#### callback_ru / callback_en / callback_ar

Добавить **один Postgres-нод** сразу после `Start`, перед Router-ом:

```
Start → [Log Event] → Router → ...существующая логика без изменений...
```

SQL для ноды `Log Event`:
```sql
INSERT INTO user_events (chat_id, event_type, event_data, language, workflow_name)
VALUES (
  {{ $json.callback_query_message_chat_id }},
  'button_click',
  '{{ $json.callback_query_data }}',
  'ru',
  'callback_ru'
);
```

Для `callback_en` — language = `'en'`, workflow_name = `'callback_en'`.
Для `callback_ar` — language = `'ar'`, workflow_name = `'callback_ar'`.

#### DAYS_ru / DAYS_en / DAYS_ar (опционально)

После каждого `Send Day N` (перед `Update Stage`) добавить Postgres-нод:

```sql
INSERT INTO user_events (chat_id, event_type, event_data, language, workflow_name)
VALUES (
  {{ $json.chat_id }},
  'funnel_message',
  'day_{{ $json.funnel_stage + 1 }}',
  'ru',
  'DAYS_ru'
);
```

### 3. Backend: новый endpoint

**Файл:** `backend/src/routes/events.ts`

```
GET /api/events/:chatId
```

Query-параметры:
- `type` (опционально) — фильтр по event_type (`button_click`, `funnel_message`)

Ответ:
```json
[
  {
    "id": 1,
    "event_type": "button_click",
    "event_data": "buy_now",
    "language": "ru",
    "workflow_name": "callback_ru",
    "created_at": "2026-02-13T10:30:00Z"
  },
  {
    "id": 2,
    "event_type": "funnel_message",
    "event_data": "day_3",
    "language": "ru",
    "workflow_name": "DAYS_ru",
    "created_at": "2026-02-14T08:00:00Z"
  }
]
```

Подключить в `backend/src/app.ts`:
```typescript
import eventsRouter from './routes/events';
app.use('/api/events', authMiddleware, eventsRouter);
```

### 4. Frontend: хук и UI

#### Хук `useUserEvents`

Файл: `frontend/src/hooks/useApi.ts`

```typescript
export interface UserEvent {
  id: number;
  event_type: string;
  event_data: string;
  language: string | null;
  workflow_name: string | null;
  created_at: string;
}

export function useUserEvents(chatId: string | null) {
  const [events, setEvents] = useState<UserEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chatId) { setEvents([]); return; }
    const fetchEvents = async () => {
      try {
        setLoading(true);
        const data = await fetchApi<UserEvent[]>(`/api/events/${chatId}`);
        setEvents(data);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to fetch events');
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, [chatId]);

  return { events, loading, error };
}
```

#### Маппинг лейблов

```typescript
export const eventLabels: Record<string, string> = {
  // callback_ru
  buy_now: 'Купить сейчас',
  show_info: 'Показать информацию',
  show_results: 'Показать результаты',
  remind_later: 'Напомнить позже',
  check_suitability: 'Проверить подходимость',
  none: 'Отказ',
  // callback_en
  nutrition_en: 'Nutrition info',
  cardio_en: 'Cardio info',
  different: 'Different option',
  beginner: 'Beginner',
  price: 'Price info',
  help: 'Help',
  coaching: 'Coaching info',
  gym: 'Gym info',
  access: 'Access',
  upgrade_79: 'Upgrade (79 AED)',
  upgrade_99: 'Upgrade (99 AED)',
  // funnel events
  day_1: 'День 1 воронки',
  day_2: 'День 2 воронки',
  day_3: 'День 3 воронки',
  day_4: 'День 4 воронки',
  day_5: 'День 5 воронки',
};
```

#### UI: объединённая timeline

В экране детального просмотра пользователя — три вкладки (Tabs):

```
[Чат]  [Действия]  [Всё]
```

- **Чат** — текущее отображение, сообщения human/ai из `n8n_chat_histories`
- **Действия** — только события из `user_events` (кнопки, воронка)
- **Всё** — merged timeline: сообщения и события, отсортированные по `created_at`

События кнопок отображаются как компактные Badge-карточки между сообщениями:

```
[ai]  Привет! Вот твой план питания...
[human]  Спасибо!

  ┌─────────────────────────────────────────┐
  │  Нажал: "Показать результаты"     14:30 │
  └─────────────────────────────────────────┘

[ai]  Вот результаты клиентов...

  ┌─────────────────────────────────────────┐
  │  Нажал: "Купить сейчас"           14:32 │
  └─────────────────────────────────────────┘
  ┌─────────────────────────────────────────┐
  │  Отправлена ссылка оплаты         14:32 │
  └─────────────────────────────────────────┘
```

Стилизация:
- `button_click` — Badge с accent цветом
- `funnel_message` — Badge с muted цветом
- `payment_link` — Badge с primary цветом
- Иконки Lucide: `MousePointerClick` для кнопок, `Mail` для воронки

---

## Сводка задач

| # | Задача | Где | Файлы |
|---|--------|-----|-------|
| 1 | Создать таблицу `user_events` | PostgreSQL | — |
| 2 | Добавить ноду Log Event в callback_ru | n8n workflow `2GGB7l9opUfOHgpo` | — |
| 3 | Добавить ноду Log Event в callback_en | n8n workflow `B6QkQPsiMrigBfY4` | — |
| 4 | Добавить ноду Log Event в callback_ar | n8n workflow `jlwgyCM5RPUxTBhG` | — |
| 5 | (Опц.) Добавить логирование в DAYS_ru/en/ar | n8n workflows | — |
| 6 | Создать endpoint `GET /api/events/:chatId` | backend | `src/routes/events.ts`, `src/app.ts` |
| 7 | Добавить хук `useUserEvents` | frontend | `src/hooks/useApi.ts` |
| 8 | Добавить маппинг `eventLabels` | frontend | `src/hooks/useApi.ts` |
| 9 | UI: вкладки Чат/Действия/Всё + timeline | frontend | `src/App.tsx` |

## Отброшенные альтернативы

1. **Писать в `n8n_chat_histories`** — ломает парсинг чата, неудобная структура для событий
2. **Читать n8n execution history через API** — много мусора, зависимость от retention policy, медленно
3. **Webhook из n8n в бэкенд** — лишний hop, n8n уже пишет в ту же PostgreSQL напрямую
