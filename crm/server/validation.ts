import { z } from 'zod';

export const chatIdParam = z.object({
  chatId: z.string().regex(/^\d{1,20}$/),
});

export const sessionIdParam = z.object({
  sessionId: z.string().regex(/^\d{1,20}$/),
});

export const usersQuery = z.object({
  search: z.string().max(100).optional(),
  status: z.enum(['buyer', 'lead']).optional(),
  goal: z.string().max(50).optional(),
  funnel_stage: z.coerce.number().int().min(0).max(6).optional(),
  sort: z.enum(['name', 'calories', 'funnel', 'age', 'weight']).optional(),
  order: z.enum(['asc', 'desc']).optional(),
});

export const recentUsersQuery = z.object({
  days: z.coerce.number().int().default(7).transform(v => Math.min(Math.max(v, 1), 365)),
  limit: z.coerce.number().int().default(20).transform(v => Math.min(Math.max(v, 1), 100)),
});

export const eventsQuery = z.object({
  type: z.string().max(50).optional(),
});
