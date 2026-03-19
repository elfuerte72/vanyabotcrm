import { Pool } from 'pg';

if (!process.env.DATABASE_URL) {
  console.error('[db] DATABASE_URL is not set');
}

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: {
    rejectUnauthorized: false
  }
});

export default pool;
