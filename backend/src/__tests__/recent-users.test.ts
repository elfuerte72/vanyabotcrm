import { describe, it, expect, vi, beforeEach } from 'vitest';
import request from 'supertest';
import app from '../app';

vi.mock('../db', () => {
  return {
    default: {
      query: vi.fn(),
    },
  };
});

import pool from '../db';
const mockQuery = vi.mocked(pool.query);

const mockUser = {
  chat_id: 123456,
  username: 'testuser',
  first_name: 'Test',
  sex: 'male',
  age: 25,
  weight: 70,
  height: 175,
  goal: 'weight_loss',
  calories: 2000,
  protein: 150,
  fats: 60,
  carbs: 200,
  funnel_stage: 3,
  is_buyer: false,
  get_food: false,
  created_at: '2026-02-10T12:00:00.000Z',
};

describe('GET /api/users/recent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns recent users sorted by created_at DESC', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [mockUser],
      command: 'SELECT',
      rowCount: 1,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/users/recent');

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(1);
    expect(res.body[0].chat_id).toBe(123456);
    expect(res.body[0].created_at).toBe('2026-02-10T12:00:00.000Z');
  });

  it('uses default days=7 and limit=20 without params', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    await request(app).get('/api/users/recent');

    expect(mockQuery).toHaveBeenCalledOnce();
    const [query, params] = mockQuery.mock.calls[0];
    expect(params).toEqual([7, 20]);
    expect(query).toContain('ORDER BY created_at DESC');
    expect(query).toContain('LIMIT $2');
  });

  it('accepts custom days parameter', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    await request(app).get('/api/users/recent?days=30');

    const [, params] = mockQuery.mock.calls[0];
    expect(params[0]).toBe(30);
  });

  it('accepts custom limit parameter', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    await request(app).get('/api/users/recent?limit=10');

    const [, params] = mockQuery.mock.calls[0];
    expect(params[1]).toBe(10);
  });

  it('clamps days to valid range (1-365)', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    await request(app).get('/api/users/recent?days=0');
    const [, params1] = mockQuery.mock.calls[0];
    expect(params1[0]).toBe(1);

    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    await request(app).get('/api/users/recent?days=999');
    const [, params2] = mockQuery.mock.calls[1];
    expect(params2[0]).toBe(365);
  });

  it('clamps limit to valid range (1-100)', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    await request(app).get('/api/users/recent?limit=0');
    const [, params1] = mockQuery.mock.calls[0];
    expect(params1[1]).toBe(1);

    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    await request(app).get('/api/users/recent?limit=500');
    const [, params2] = mockQuery.mock.calls[1];
    expect(params2[1]).toBe(100);
  });

  it('returns empty array when no recent users', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/users/recent');

    expect(res.status).toBe(200);
    expect(res.body).toEqual([]);
  });

  it('returns 500 when database fails', async () => {
    mockQuery.mockRejectedValueOnce(new Error('Connection refused'));

    const res = await request(app).get('/api/users/recent');

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('Failed to fetch recent users');
  });
});
