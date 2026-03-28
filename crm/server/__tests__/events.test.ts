import { describe, it, expect, vi, beforeEach } from 'vitest';
import request from 'supertest';
import app from '../app.js';

vi.mock('../db.js', () => {
  return {
    default: {
      query: vi.fn(),
    },
  };
});

import pool from '../db.js';
const mockQuery = vi.mocked(pool.query);

describe('GET /api/events/:chatId', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns events for a valid chatId', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          id: 1,
          chat_id: 12345,
          event_type: 'button_click',
          event_data: 'buy_now',
          language: 'ru',
          workflow_name: 'funnel',
          created_at: '2026-03-28T10:00:00Z',
        },
        {
          id: 2,
          chat_id: 12345,
          event_type: 'funnel_message',
          event_data: 'stage_0',
          language: 'ru',
          workflow_name: 'funnel',
          created_at: '2026-03-28T09:00:00Z',
        },
      ],
      command: 'SELECT',
      rowCount: 2,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/events/12345');

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(2);
    expect(res.body[0].event_type).toBe('button_click');
    expect(res.body[0].event_data).toBe('buy_now');
    expect(res.body[0].language).toBe('ru');
    expect(res.body[0].workflow_name).toBe('funnel');
    expect(res.body[1].event_type).toBe('funnel_message');
    expect(res.body[1].event_data).toBe('stage_0');
  });

  it('returns empty array when no events exist', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/events/99999');

    expect(res.status).toBe(200);
    expect(res.body).toEqual([]);
  });

  it('filters by event type when ?type= is provided', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          id: 1,
          chat_id: 12345,
          event_type: 'button_click',
          event_data: 'buy_now',
          language: 'en',
          workflow_name: 'funnel',
          created_at: '2026-03-28T10:00:00Z',
        },
      ],
      command: 'SELECT',
      rowCount: 1,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/events/12345?type=button_click');

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(1);

    const [query, params] = mockQuery.mock.calls[0];
    expect(query).toContain('event_type = $2');
    expect(params).toEqual(['12345', 'button_click']);
  });

  it('queries with correct chatId parameter', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    await request(app).get('/api/events/7829526925');

    expect(mockQuery).toHaveBeenCalledOnce();
    const [query, params] = mockQuery.mock.calls[0];
    expect(query).toContain('chat_id = $1');
    expect(query).toContain('ORDER BY created_at ASC');
    expect(params[0]).toBe('7829526925');
  });

  it('returns 500 when database fails', async () => {
    mockQuery.mockRejectedValueOnce(new Error('Connection refused'));

    const res = await request(app).get('/api/events/12345');

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('Failed to fetch user events');
  });

  it('returns 400 for invalid chatId', async () => {
    const res = await request(app).get('/api/events/not-a-number');

    expect(res.status).toBe(400);
  });
});
