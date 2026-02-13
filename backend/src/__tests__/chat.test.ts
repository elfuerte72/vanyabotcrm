import { describe, it, expect, vi, beforeEach } from 'vitest';
import request from 'supertest';
import app from '../app';

// Mock the database pool
vi.mock('../db', () => {
  return {
    default: {
      query: vi.fn(),
    },
  };
});

import pool from '../db';
const mockQuery = vi.mocked(pool.query);

describe('GET /api/chat/:sessionId', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns formatted messages for a valid session', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          id: 1,
          session_id: '123456',
          message: {
            type: 'human',
            content: 'Привет!',
            tool_calls: [],
          },
        },
        {
          id: 2,
          session_id: '123456',
          message: {
            type: 'ai',
            content: 'Привет! Я Иван, твой помощник по питанию.',
            tool_calls: [],
          },
        },
      ],
      command: 'SELECT',
      rowCount: 2,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/chat/123456');

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(2);
    expect(res.body[0]).toEqual({
      id: 1,
      type: 'human',
      content: 'Привет!',
      tool_calls: [],
    });
    expect(res.body[1]).toEqual({
      id: 2,
      type: 'ai',
      content: 'Привет! Я Иван, твой помощник по питанию.',
      tool_calls: [],
    });
  });

  it('returns empty array when no chat history exists', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/chat/999999999');

    expect(res.status).toBe(200);
    expect(res.body).toEqual([]);
  });

  it('handles messages with missing content gracefully', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          id: 1,
          session_id: '123',
          message: {
            type: 'ai',
            content: '',
            tool_calls: [{ name: 'calculate_macros', args: {} }],
          },
        },
        {
          id: 2,
          session_id: '123',
          message: {
            type: 'ai',
            // content is missing entirely
          },
        },
      ],
      command: 'SELECT',
      rowCount: 2,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/chat/123');

    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(2);
    // Empty content string
    expect(res.body[0].content).toBe('');
    expect(res.body[0].tool_calls).toEqual([{ name: 'calculate_macros', args: {} }]);
    // Missing content defaults to ''
    expect(res.body[1].content).toBe('');
    expect(res.body[1].type).toBe('ai');
  });

  it('handles messages with missing type', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          id: 1,
          session_id: '123',
          message: {
            content: 'Some message without type',
          },
        },
      ],
      command: 'SELECT',
      rowCount: 1,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/chat/123');

    expect(res.status).toBe(200);
    expect(res.body[0].type).toBe('unknown');
    expect(res.body[0].content).toBe('Some message without type');
  });

  it('queries database with correct session_id parameter', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    await request(app).get('/api/chat/7829526925');

    expect(mockQuery).toHaveBeenCalledOnce();
    const [query, params] = mockQuery.mock.calls[0];
    expect(params).toEqual(['7829526925']);
    expect(query).toContain('session_id = $1');
    expect(query).toContain('ORDER BY id ASC');
  });

  it('returns 500 when database fails', async () => {
    mockQuery.mockRejectedValueOnce(new Error('Connection refused'));

    const res = await request(app).get('/api/chat/123456');

    expect(res.status).toBe(500);
    expect(res.body.error).toBe('Failed to fetch chat history');
  });

  it('preserves tool_calls from AI messages', async () => {
    const toolCalls = [
      {
        name: 'save_user_data',
        args: { sex: 'male', weight: 70, height: 160, age: 29 },
      },
    ];

    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          id: 10,
          session_id: '379336096',
          message: {
            type: 'ai',
            content: 'Отлично, всё зафиксировал!',
            tool_calls: toolCalls,
          },
        },
      ],
      command: 'SELECT',
      rowCount: 1,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/chat/379336096');

    expect(res.status).toBe(200);
    expect(res.body[0].tool_calls).toEqual(toolCalls);
  });

  it('returns messages in correct order (ASC by id)', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        { id: 1, session_id: '100', message: { type: 'human', content: 'First' } },
        { id: 2, session_id: '100', message: { type: 'ai', content: 'Second' } },
        { id: 5, session_id: '100', message: { type: 'human', content: 'Third' } },
      ],
      command: 'SELECT',
      rowCount: 3,
      oid: 0,
      fields: [],
    } as any);

    const res = await request(app).get('/api/chat/100');

    expect(res.status).toBe(200);
    expect(res.body.map((m: any) => m.id)).toEqual([1, 2, 5]);
    expect(res.body.map((m: any) => m.content)).toEqual(['First', 'Second', 'Third']);
  });
});

describe('Chat history data integrity', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('session_id is passed as string (matching chat_id::text)', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [],
      command: 'SELECT',
      rowCount: 0,
      oid: 0,
      fields: [],
    } as any);

    // Frontend passes chat_id as String(user.chat_id)
    const chatId = 7829526925;
    await request(app).get(`/api/chat/${String(chatId)}`);

    const [, params] = mockQuery.mock.calls[0];
    // Verify it's passed as string, not number
    expect(typeof params[0]).toBe('string');
    expect(params[0]).toBe('7829526925');
  });
});
