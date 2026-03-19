-- Rename legacy n8n_chat_histories table to chat_histories
-- Run this migration before deploying updated bot/CRM code

BEGIN;

ALTER TABLE n8n_chat_histories RENAME TO chat_histories;
ALTER SEQUENCE n8n_chat_histories_id_seq RENAME TO chat_histories_id_seq;
ALTER INDEX n8n_chat_histories_pkey RENAME TO chat_histories_pkey;

-- Backward-compatible view for transition period
CREATE VIEW n8n_chat_histories AS SELECT * FROM chat_histories;

COMMIT;

-- After both bot and CRM are deployed with new table name:
-- DROP VIEW n8n_chat_histories;
