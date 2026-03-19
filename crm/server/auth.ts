import { Request, Response, NextFunction } from 'express';
import { validate, parse } from '@telegram-apps/init-data-node';

const BOT_TOKEN = process.env.BOT_TOKEN || '';

export const authMiddleware = (req: Request, res: Response, next: NextFunction) => {
  // Skip auth in development if no BOT_TOKEN
  if (!BOT_TOKEN) {
    return next();
  }

  const authHeader = req.header('authorization') || '';
  const [authType, authData] = authHeader.split(' ');

  if (authType !== 'tma' || !authData) {
    return res.status(401).json({ error: 'Unauthorized: Missing or invalid authorization header' });
  }

  try {
    validate(authData, BOT_TOKEN, { expiresIn: 3600 });
    (req as any).initData = parse(authData);
    next();
  } catch (e) {
    console.error('[auth] Validation error:', e);
    res.status(401).json({ error: 'Invalid init data' });
  }
};
