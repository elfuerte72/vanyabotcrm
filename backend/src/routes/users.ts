import { Router, Request, Response } from 'express';
import pool from '../db';

const router = Router();

// GET /api/users - список пользователей с фильтрацией
router.get('/', async (req: Request, res: Response) => {
  try {
    const { search, status, goal, funnel_stage, sort, order } = req.query;

    const conditions: string[] = [];
    const params: any[] = [];
    let paramIdx = 1;

    // Поиск по имени, username, chat_id
    if (search && typeof search === 'string' && search.trim()) {
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
      conditions.push(`is_buyer = true`);
    } else if (status === 'lead') {
      conditions.push(`is_buyer = false`);
    }

    // Фильтр по цели
    if (goal && typeof goal === 'string' && goal.trim()) {
      conditions.push(`goal = $${paramIdx}`);
      params.push(goal.trim());
      paramIdx++;
    }

    // Фильтр по этапу воронки
    if (funnel_stage !== undefined && funnel_stage !== '' && funnel_stage !== null) {
      const stage = parseInt(funnel_stage as string, 10);
      if (!isNaN(stage)) {
        conditions.push(`funnel_stage = $${paramIdx}`);
        params.push(stage);
        paramIdx++;
      }
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
    const sortColumn = allowedSorts[(sort as string)] || 'is_buyer DESC, funnel_stage';
    const sortOrder = order === 'asc' ? 'ASC' : 'DESC';
    const orderClause = sort
      ? `ORDER BY ${sortColumn} ${sortOrder} NULLS LAST`
      : `ORDER BY is_buyer DESC, funnel_stage DESC, first_name`;

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
    console.error('Error fetching users:', error);
    res.status(500).json({ error: 'Failed to fetch users' });
  }
});

// GET /api/users/recent - последние добавленные клиенты
router.get('/recent', async (req: Request, res: Response) => {
  try {
    const parsedDays = parseInt(req.query.days as string, 10);
    const days = Math.min(Math.max(isNaN(parsedDays) ? 7 : parsedDays, 1), 365);
    const parsedLimit = parseInt(req.query.limit as string, 10);
    const limit = Math.min(Math.max(isNaN(parsedLimit) ? 20 : parsedLimit, 1), 100);

    console.log(`[users.recent] Fetching recent users`, { days, limit });

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

    console.log(`[users.recent] Found ${result.rows.length} users`);
    res.json(result.rows);
  } catch (error) {
    console.error('[users.recent] Error:', error);
    res.status(500).json({ error: 'Failed to fetch recent users' });
  }
});

// GET /api/users/:chatId - детали пользователя
router.get('/:chatId', async (req: Request, res: Response) => {
  try {
    const { chatId } = req.params;

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
    console.error('Error fetching user:', error);
    res.status(500).json({ error: 'Failed to fetch user' });
  }
});

export default router;
