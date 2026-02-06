import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgres://railway:y6G7oBq6-0VdfPV3S6HuliVFeL2d4tMa@yamabiko.proxy.rlwy.net:26903/railway',
  ssl: {
    rejectUnauthorized: false
  }
});

export default pool;
