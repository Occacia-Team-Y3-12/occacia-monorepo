export type CustomerPersona = {
  id: number;
  persona_id: string;
  customer_id: string;
  name: string;
  relationship: string | null;
  birthday: string | null;
  personality: string | null;
  preferences_json: unknown | null;
  food_preferences: string[];
  color_preferences: string[];
  music_preferences: string[];
  personality_tags: string[];
  is_confirmed: boolean;
  confirmed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type CustomerPersonaUpdatePayload = {
  name?: string;
  relationship?: string | null;
  birthday?: string | null;
  personality?: string | null;
  preferences_json?: unknown | null;
  food_preferences?: string[];
  color_preferences?: string[];
  music_preferences?: string[];
  personality_tags?: string[];
};

export type CustomerPersonaDraft = {
  name: string;
  relationship: string;
  birthday: string;
  personality: string;
  preferences_json: unknown | null;
  food_preferences: string[];
  color_preferences: string[];
  music_preferences: string[];
  personality_tags: string[];
};
