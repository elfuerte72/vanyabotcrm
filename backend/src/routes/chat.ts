import { Router, Request, Response } from 'express';
import pool from '../db';

const router = Router();

interface ChatMessage {
  type: string;
  content: string;
  tool_calls?: any[];
  additional_kwargs?: any;
  response_metadata?: any;
}

// GET /api/chat/:sessionId - история чата
router.get('/:sessionId', async (req: Request, res: Response) => {
  try {
    const { sessionId } = req.params;

    const result = await pool.query(`
      SELECT
        id,
        session_id,
        message
      FROM n8n_chat_histories
      WHERE session_id = $1
      ORDER BY id ASC
    `, [sessionId]);

    // Преобразуем JSONB message в удобный формат
    const messages = result.rows.map(row => {
      const msg = row.message as ChatMessage;
      return {
        id: row.id,
        type: msg.type || 'unknown',
        content: msg.content || '',
        tool_calls: msg.tool_calls || []
      };
    });

    res.json(messages);
  } catch (error) {
    console.error('Error fetching chat history:', error);
    res.status(500).json({ error: 'Failed to fetch chat history' });
  }
});

export default router;
