import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import pinoHttp from 'pino-http';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
import logger from './logger.js';
import { authMiddleware } from './auth.js';
import usersRouter from './modules/users/routes.js';
import chatRouter from './modules/chat/routes.js';
import statsRouter from './modules/stats/routes.js';
import eventsRouter from './modules/events/routes.js';

const app = express();
app.set('trust proxy', true);

const isProduction = process.env.NODE_ENV === 'production';

// Security headers — allow Telegram Web App SDK
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      ...helmet.contentSecurityPolicy.getDefaultDirectives(),
      'script-src': ["'self'", "https://telegram.org"],
    },
  },
}));

// CORS: in production SPA is served by the same server (no CORS needed)
// In dev, allow Vite dev server
app.use(cors({
  origin: isProduction ? false : 'http://localhost:5173',
  credentials: true,
}));

// Body parser with size limit
app.use(express.json({ limit: '100kb' }));

// Request logging
// @ts-expect-error pino-http CJS default export not callable under NodeNext
app.use(pinoHttp({ logger }));

// Rate limiting on API routes
const apiLimiter = rateLimit({
  windowMs: 60_000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api', apiLimiter);

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
  logger.error({ err }, 'Unhandled error');
  res.status(500).json({ error: 'Internal server error' });
});

// Serve frontend static files in production
const frontendPath = path.join(__dirname, 'public');
app.use(express.static(frontendPath));
app.get('*', (req, res) => {
  res.sendFile(path.join(frontendPath, 'index.html'));
});

export default app;
