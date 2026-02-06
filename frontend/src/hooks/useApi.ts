import { useState, useEffect, useCallback, useRef } from 'react';

const API_URL = import.meta.env.VITE_API_URL || '';

function getInitData(): string {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp?.initData) {
    return window.Telegram.WebApp.initData;
  }
  return '';
}

async function fetchApi<T>(endpoint: string): Promise<T> {
  const initData = getInitData();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (initData) {
    headers['Authorization'] = `tma ${initData}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, { headers });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Shared label constants
export const goalLabels: Record<string, string> = {
  weight_loss: 'Похудение',
  weight_gain: 'Набор массы',
  maintenance: 'Поддержание',
  muscle_gain: 'Набор мышц',
};

export const activityLabels: Record<string, string> = {
  sedentary: 'Сидячий образ жизни',
  light: 'Лёгкая активность',
  moderate: 'Умеренная активность',
  active: 'Высокая активность',
  very_active: 'Очень высокая активность',
};

export interface User {
  chat_id: number;
  username: string | null;
  first_name: string | null;
  sex: string | null;
  age: number | null;
  weight: number | null;
  height: number | null;
  activity_level?: string | null;
  goal: string | null;
  allergies?: string | null;
  excluded_foods?: string | null;
  calories: number | null;
  protein: number | null;
  fats: number | null;
  carbs: number | null;
  funnel_stage: number | null;
  is_buyer: boolean;
  get_food: boolean;
  language?: string | null;
}

export interface ChatMessage {
  id: number;
  type: 'human' | 'ai' | string;
  content: string;
  tool_calls: any[];
}

export interface UserFilters {
  search?: string;
  status?: 'all' | 'buyer' | 'lead';
  goal?: string;
  funnel_stage?: string;
}

export interface Stats {
  total_users: number;
  buyers: number;
  leads: number;
  avg_calories: number;
  avg_protein: number;
  avg_fats: number;
  avg_carbs: number;
  goal_distribution: { goal: string; count: number }[];
  funnel_distribution: { stage: number; count: number }[];
}

function buildQueryString(filters: UserFilters): string {
  const params = new URLSearchParams();
  if (filters.search) params.set('search', filters.search);
  if (filters.status && filters.status !== 'all') params.set('status', filters.status);
  if (filters.goal) params.set('goal', filters.goal);
  if (filters.funnel_stage) params.set('funnel_stage', filters.funnel_stage);
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}

export function useUsers(filters: UserFilters = {}) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchUsers = useCallback(async (f: UserFilters) => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    try {
      setLoading(true);
      const qs = buildQueryString(f);
      const data = await fetchApi<User[]>(`/api/users${qs}`);
      setUsers(data);
      setError(null);
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return;
      setError(e instanceof Error ? e.message : 'Failed to fetch users');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers(filters);
  }, [filters.search, filters.status, filters.goal, filters.funnel_stage, fetchUsers]);

  return { users, loading, error, refetch: () => fetchUsers(filters) };
}

export function useUser(chatId: string | null) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chatId) {
      setUser(null);
      return;
    }

    const fetchUser = async () => {
      try {
        setLoading(true);
        const data = await fetchApi<User>(`/api/users/${chatId}`);
        setUser(data);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to fetch user');
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [chatId]);

  return { user, loading, error };
}

export function useStats() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const data = await fetchApi<Stats>('/api/stats');
        setStats(data);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to fetch stats');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return { stats, loading, error };
}

export function useChatHistory(sessionId: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }

    const fetchChat = async () => {
      try {
        setLoading(true);
        const data = await fetchApi<ChatMessage[]>(`/api/chat/${sessionId}`);
        setMessages(data);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to fetch chat');
      } finally {
        setLoading(false);
      }
    };

    fetchChat();
  }, [sessionId]);

  return { messages, loading, error };
}
