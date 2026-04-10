import { Router, Request, Response } from 'express';
import pool from '../../db.js';
import logger from '../../logger.js';
import { chatIdParam, eventsQuery } from '../../validation.js';

const router = Router();

// GET /api/events/:chatId - события пользователя (кнопки, воронка)
router.get('/:chatId', async (req: Request, res: Response) => {
  try {
    const paramsParsed = chatIdParam.safeParse(req.params);
    if (!paramsParsed.success) {
      return res.status(400).json({ error: 'Invalid chatId parameter' });
    }

    const queryParsed = eventsQuery.safeParse(req.query);
    if (!queryParsed.success) {
      return res.status(400).json({ error: 'Invalid query parameters' });
    }

    const { chatId } = paramsParsed.data;
    const { type } = queryParsed.data;

    let query = `
      SELECT id, chat_id, event_type, event_data, language, workflow_name, message_text, created_at
      FROM user_events
      WHERE chat_id = $1
    `;
    const params: (string | number)[] = [chatId];

    if (type) {
      query += ` AND event_type = $2`;
      params.push(type);
    }

    query += ` ORDER BY created_at ASC`;

    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch (error) {
    logger.error({ err: error }, 'Error fetching user events');
    res.status(500).json({ error: 'Failed to fetch user events' });
  }
});

export default router;
