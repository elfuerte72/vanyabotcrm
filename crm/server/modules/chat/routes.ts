import { Router, Request, Response } from 'express';
import pool from '../../db.js';
import logger from '../../logger.js';
import { sessionIdParam } from '../../validation.js';
import type { ChatMessage } from '../../../shared/types.js';

const router = Router();

interface DBChatMessage {
  type: string;
  content: string;
  tool_calls?: any[];
  additional_kwargs?: any;
  response_metadata?: any;
}

// GET /api/chat/:sessionId - история чата
router.get('/:sessionId', async (req: Request, res: Response) => {
  try {
    const parsed = sessionIdParam.safeParse(req.params);
    if (!parsed.success) {
      return res.status(400).json({ error: 'Invalid sessionId parameter' });
    }

    const { sessionId } = parsed.data;

    const result = await pool.query(`
      SELECT
        id,
        session_id,
        message
      FROM chat_histories
      WHERE session_id = $1
      ORDER BY id ASC
    `, [sessionId]);

    // Преобразуем JSONB message в удобный формат
    const messages: ChatMessage[] = result.rows.map(row => {
      const msg = row.message as DBChatMessage;
      return {
        id: row.id,
        type: msg.type || 'unknown',
        content: msg.content || '',
        tool_calls: msg.tool_calls || []
      };
    });

    res.json(messages);
  } catch (error) {
    logger.error({ err: error }, 'Error fetching chat history');
    res.status(500).json({ error: 'Failed to fetch chat history' });
  }
});

export default router;
