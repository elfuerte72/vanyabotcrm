import app from './app.js';
import logger from './logger.js';

const PORT = process.env.PORT || 3001;

app.listen(PORT, () => {
  logger.info({ port: PORT }, 'Server started');
  if (!process.env.BOT_TOKEN) {
    logger.warn('BOT_TOKEN not configured — auth validation disabled');
  }
});
