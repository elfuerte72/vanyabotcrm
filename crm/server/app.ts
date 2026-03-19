import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
import { authMiddleware } from './auth.js';
import usersRouter from './modules/users/routes.js';
import chatRouter from './modules/chat/routes.js';
import statsRouter from './modules/stats/routes.js';
import eventsRouter from './modules/events/routes.js';

const app = express();

// Middleware
app.use(cors({
  origin: true,
  credentials: true
}));
app.use(express.json());

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
  console.error('[app] Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// Serve frontend static files in production
const frontendPath = path.join(__dirname, 'public');
app.use(express.static(frontendPath));
app.get('*', (req, res) => {
  res.sendFile(path.join(frontendPath, 'index.html'));
});

export default app;
