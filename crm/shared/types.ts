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
  funnel_variant: string | null;
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

export interface UserEvent {
  id: number;
  chat_id: number;
  event_type: string;
  event_data: string;
  language: string | null;
  workflow_name: string | null;
  created_at: string;
}

export type Goal = 'weight_loss' | 'weight_gain' | 'maintenance' | 'muscle_gain';

export type ActivityLevel = 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active';
