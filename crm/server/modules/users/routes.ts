import { Router, Request, Response } from 'express';
import pool from '../../db.js';
import logger from '../../logger.js';
import { usersQuery, recentUsersQuery, chatIdParam } from '../../validation.js';

const router = Router();

// GET /api/users - список пользователей с фильтрацией
router.get('/', async (req: Request, res: Response) => {
  try {
    const parsed = usersQuery.safeParse(req.query);
    if (!parsed.success) {
      return res.status(400).json({ error: 'Invalid query parameters', details: parsed.error.flatten() });
    }

    const { search, status, goal, funnel_stage, sort, order } = parsed.data;

    const conditions: string[] = [];
    const params: any[] = [];
    let paramIdx = 1;

    // Поиск по имени, username, chat_id
    if (search && search.trim()) {
      conditions.push(`(
        first_name ILIKE $${paramIdx}
        OR username ILIKE $${paramIdx}
        OR chat_id::text ILIKE $${paramIdx}
      )`);
      params.push(`%${search.trim()}%`);
      paramIdx++;
    }

    // Фильтр по статусу (buyer / lead)
    if (status === 'buyer') {
      conditions.push(`is_buyer = $${paramIdx}`);
      params.push(true);
      paramIdx++;
    } else if (status === 'lead') {
      conditions.push(`is_buyer = $${paramIdx}`);
      params.push(false);
      paramIdx++;
    }

    // Фильтр по цели
    if (goal && goal.trim()) {
      conditions.push(`goal = $${paramIdx}`);
      params.push(goal.trim());
      paramIdx++;
    }

    // Фильтр по этапу воронки
    if (funnel_stage !== undefined) {
      conditions.push(`funnel_stage = $${paramIdx}`);
      params.push(funnel_stage);
      paramIdx++;
    }

    const whereClause = conditions.length > 0
      ? `WHERE ${conditions.join(' AND ')}`
      : '';

    // Сортировка
    const allowedSorts: Record<string, string> = {
      name: 'first_name',
      calories: 'calories',
      funnel: 'funnel_stage',
      age: 'age',
      weight: 'weight',
    };
    const sortColumn = allowedSorts[sort as string] || 'is_buyer DESC, funnel_stage';
    const sortOrder = order === 'asc' ? 'ASC' : 'DESC';
    const orderClause = sort
      ? `ORDER BY ${sortColumn} ${sortOrder} NULLS LAST`
      : `ORDER BY updated_at DESC NULLS LAST, created_at DESC`;

    const result = await pool.query(`
      SELECT
        chat_id,
        username,
        first_name,
        sex,
        age,
        weight,
        height,
        goal,
        calories,
        protein,
        fats,
        carbs,
        funnel_stage,
        is_buyer,
        get_food,
        created_at
      FROM users_nutrition
      ${whereClause}
      ${orderClause}
    `, params);

    res.json(result.rows);
  } catch (error) {
    logger.error({ err: error }, 'Error fetching users');
    res.status(500).json({ error: 'Failed to fetch users' });
  }
});

// GET /api/users/recent - последние добавленные клиенты
router.get('/recent', async (req: Request, res: Response) => {
  try {
    const parsed = recentUsersQuery.safeParse(req.query);
    if (!parsed.success) {
      return res.status(400).json({ error: 'Invalid query parameters', details: parsed.error.flatten() });
    }

    const { days, limit } = parsed.data;

    const result = await pool.query(`
      SELECT
        chat_id,
        username,
        first_name,
        sex,
        age,
        weight,
        height,
        goal,
        calories,
        protein,
        fats,
        carbs,
        funnel_stage,
        is_buyer,
        get_food,
        created_at
      FROM users_nutrition
      WHERE created_at >= NOW() - INTERVAL '1 day' * $1
      ORDER BY created_at DESC
      LIMIT $2
    `, [days, limit]);

    res.json(result.rows);
  } catch (error) {
    logger.error({ err: error }, 'Error fetching recent users');
    res.status(500).json({ error: 'Failed to fetch recent users' });
  }
});

// GET /api/users/:chatId - детали пользователя
router.get('/:chatId', async (req: Request, res: Response) => {
  try {
    const parsed = chatIdParam.safeParse(req.params);
    if (!parsed.success) {
      return res.status(400).json({ error: 'Invalid chatId parameter' });
    }

    const { chatId } = parsed.data;

    const result = await pool.query(`
      SELECT
        chat_id,
        username,
        first_name,
        sex,
        age,
        weight,
        height,
        activity_level,
        goal,
        allergies,
        excluded_foods,
        calories,
        protein,
        fats,
        carbs,
        funnel_stage,
        is_buyer,
        get_food,
        language,
        created_at
      FROM users_nutrition
      WHERE chat_id = $1
    `, [chatId]);

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json(result.rows[0]);
  } catch (error) {
    logger.error({ err: error }, 'Error fetching user');
    res.status(500).json({ error: 'Failed to fetch user' });
  }
});

export default router;
