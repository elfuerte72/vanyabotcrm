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
  created_at?: string | null;
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

// Human-readable labels for callback button names
// Based on actual Telegram bot inline keyboard button texts
export const eventButtonLabels: Record<string, { label: string; botResponse: string }> = {
  // callback_ru
  buy_now: { label: 'Купить сейчас', botResponse: 'Отправлена ссылка на оплату' },
  show_info: { label: 'Подробнее о программе', botResponse: 'Отправлено видео с информацией' },
  show_results: { label: 'Результаты клиентов', botResponse: 'Отправлено фото результатов' },
  remind_later: { label: 'Напомнить позже', botResponse: 'Отправлено мотивационное сообщение' },
  check_suitability: { label: 'Подходит ли мне?', botResponse: 'Отправлено видео о подходимости' },
  none: { label: 'Отказ от покупки', botResponse: 'Отправлено прощальное сообщение' },
  // callback_en
  nutrition_en: { label: 'Nutrition info', botResponse: 'Sent nutrition + training explanation' },
  cardio_en: { label: 'Cardio vs Muscle', botResponse: 'Sent cardio vs strength training info' },
  different: { label: 'What makes it different?', botResponse: 'Sent unique program explanation' },
  beginner: { label: 'I\'m a beginner', botResponse: 'Sent beginner-friendly explanation' },
  price: { label: 'Why this price?', botResponse: 'Sent pricing explanation (49 AED)' },
  help: { label: 'Help', botResponse: 'Sent program summary + access info' },
  coaching: { label: 'Coaching options', botResponse: 'Sent coaching packages (79/99 AED)' },
  gym: { label: 'What gym do I need?', botResponse: 'Sent gym requirements (barbell + dumbbells)' },
  access: { label: 'Get access', botResponse: 'Sent access details + payment info' },
  upgrade_79: { label: 'Technique Check (79 AED)', botResponse: 'Создан заказ Ziina, отправлена ссылка' },
  upgrade_99: { label: '7-Day Coaching (99 AED)', botResponse: 'Создан заказ Ziina, отправлена ссылка' },
  // funnel day events
  day_1: { label: 'День 1 воронки', botResponse: 'Отправлено сообщение дня 1' },
  day_2: { label: 'День 2 воронки', botResponse: 'Отправлено сообщение дня 2' },
  day_3: { label: 'День 3 воронки', botResponse: 'Отправлено сообщение дня 3' },
  day_4: { label: 'День 4 воронки', botResponse: 'Отправлено сообщение дня 4' },
  day_5: { label: 'День 5 воронки', botResponse: 'Отправлено сообщение дня 5' },
};

export interface UserEvent {
  id: number;
  chat_id: number;
  event_type: string;
  event_data: string;
  language: string | null;
  workflow_name: string | null;
  created_at: string;
}

export function useUserEvents(chatId: string | null) {
  const [events, setEvents] = useState<UserEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chatId) { setEvents([]); return; }
    const fetchEvents = async () => {
      try {
        setLoading(true);
        const data = await fetchApi<UserEvent[]>(`/api/events/${chatId}`);
        setEvents(data);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to fetch events');
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, [chatId]);

  return { events, loading, error };
}

export function useRecentUsers(days = 7, limit = 50) {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecent = useCallback(async (d: number, l: number) => {
    try {
      setLoading(true);
      const data = await fetchApi<User[]>(`/api/users/recent?days=${d}&limit=${l}`);
      setUsers(data);
      setError(null);
    } catch (e) {
      console.error('[useRecentUsers] Error fetching recent users:', e);
      setError(e instanceof Error ? e.message : 'Failed to fetch recent users');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRecent(days, limit);
  }, [days, limit, fetchRecent]);

  return { users, loading, error, refetch: () => fetchRecent(days, limit) };
}
