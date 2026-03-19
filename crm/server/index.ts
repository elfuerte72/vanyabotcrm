import app from './app.js';

const PORT = process.env.PORT || 3001;

app.listen(PORT, () => {
  console.log(`[server] Running on port ${PORT}`);
  if (!process.env.BOT_TOKEN) {
    console.warn('[server] BOT_TOKEN not configured - auth validation disabled');
  }
});
