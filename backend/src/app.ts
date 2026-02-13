import express from 'express';
import cors from 'cors';
import path from 'path';
import { validate, parse } from '@telegram-apps/init-data-node';
import usersRouter from './routes/users';
import chatRouter from './routes/chat';
import statsRouter from './routes/stats';
import eventsRouter from './routes/events';

const app = express();
const BOT_TOKEN = process.env.BOT_TOKEN || '';

// Middleware
app.use(cors({
  origin: true,
  credentials: true
}));
app.use(express.json());

// Telegram initData auth middleware
const authMiddleware = (req: express.Request, res: express.Response, next: express.NextFunction) => {
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
    console.error('Auth validation error:', e);
    res.status(401).json({ error: 'Invalid init data' });
  }
};

// Health check (no auth)
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Protected API routes
app.use('/api/users', authMiddleware, usersRouter);
app.use('/api/chat', authMiddleware, chatRouter);
app.use('/api/stats', authMiddleware, statsRouter);
app.use('/api/events', authMiddleware, eventsRouter);

// Error handler
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Serve frontend static files in production
const frontendPath = path.join(__dirname, '..', 'public');
app.use(express.static(frontendPath));
app.get('*', (req, res) => {
  res.sendFile(path.join(frontendPath, 'index.html'));
});

export default app;
