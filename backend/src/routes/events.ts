import { Router, Request, Response } from 'express';
import pool from '../db';

const router = Router();

// GET /api/events/:chatId - события пользователя (кнопки, воронка)
router.get('/:chatId', async (req: Request, res: Response) => {
  try {
    const { chatId } = req.params;
    const { type } = req.query;

    let query = `
      SELECT id, chat_id, event_type, event_data, language, workflow_name, created_at
      FROM user_events
      WHERE chat_id = $1
    `;
    const params: (string | number)[] = [chatId];

    if (type) {
      query += ` AND event_type = $2`;
      params.push(String(type));
    }

    query += ` ORDER BY created_at ASC`;

    const result = await pool.query(query, params);
    res.json(result.rows);
  } catch (error) {
    console.error('Error fetching user events:', error);
    res.status(500).json({ error: 'Failed to fetch user events' });
  }
});

export default router;
