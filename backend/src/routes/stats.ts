import { Router, Request, Response } from 'express';
import pool from '../db';

const router = Router();

// GET /api/stats - агрегированная статистика
router.get('/', async (req: Request, res: Response) => {
  try {
    const [totals, goalDist, funnelDist] = await Promise.all([
      pool.query(`
        SELECT
          COUNT(*)::int AS total_users,
          COUNT(*) FILTER (WHERE is_buyer = true)::int AS buyers,
          COUNT(*) FILTER (WHERE is_buyer = false)::int AS leads,
          ROUND(AVG(calories))::int AS avg_calories,
          ROUND(AVG(protein))::int AS avg_protein,
          ROUND(AVG(fats))::int AS avg_fats,
          ROUND(AVG(carbs))::int AS avg_carbs
        FROM users_nutrition
      `),
      pool.query(`
        SELECT COALESCE(goal, 'unknown') AS goal, COUNT(*)::int AS count
        FROM users_nutrition
        GROUP BY goal
        ORDER BY count DESC
      `),
      pool.query(`
        SELECT COALESCE(funnel_stage, 0) AS stage, COUNT(*)::int AS count
        FROM users_nutrition
        GROUP BY funnel_stage
        ORDER BY stage
      `)
    ]);

    res.json({
      ...totals.rows[0],
      goal_distribution: goalDist.rows,
      funnel_distribution: funnelDist.rows,
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Failed to fetch stats' });
  }
});

export default router;
