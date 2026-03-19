import { Request, Response, NextFunction } from 'express';
import { validate, parse } from '@telegram-apps/init-data-node';
import logger from './logger.js';

const BOT_TOKEN = process.env.BOT_TOKEN || '';

// In production, BOT_TOKEN must be set
if (process.env.NODE_ENV === 'production' && !BOT_TOKEN) {
  throw new Error('BOT_TOKEN is required in production');
}

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
    logger.warn({ err: e }, 'Auth validation failed');
    res.status(401).json({ error: 'Invalid init data' });
  }
};
