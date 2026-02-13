import app from './app';

const PORT = process.env.PORT || 3001;

app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  if (!process.env.BOT_TOKEN) {
    console.warn('⚠️ BOT_TOKEN not configured - auth validation disabled');
  }
});
