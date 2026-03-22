# Pre-deploy checklist (feature/funnel-ru-rework)

## База данных

- [ ] Применить миграцию `db/migrations/002_add_next_funnel_msg_at.sql`:
  ```sql
  ALTER TABLE users_nutrition ADD COLUMN IF NOT EXISTS next_funnel_msg_at TIMESTAMPTZ;
  ```

## Медиа

- [ ] Заменить placeholder file IDs в `bot/config/media.yaml` → `video_notes` на реальные ID кружочков (квадратное видео, max 640x640, до 1 мин)
- [ ] Проверить что фото `bot/media/photos/before_after_1.jpg` и `before_after_2.jpg` корректные
