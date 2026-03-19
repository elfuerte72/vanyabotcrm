import { Pool } from 'pg';
import logger from './logger.js';

if (!process.env.DATABASE_URL) {
  logger.error('DATABASE_URL is not set');
}

const dsn = process.env.DATABASE_URL || '';
const sslDisabled = dsn.includes('sslmode=disable');

const pool = new Pool({
  connectionString: dsn,
  ssl: sslDisabled ? false : true,
});

export default pool;
