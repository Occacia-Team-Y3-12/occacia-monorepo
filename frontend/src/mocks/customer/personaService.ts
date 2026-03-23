import type { ServiceResult } from '@/types/customer';
import type {
  CustomerPersona,
  CustomerPersonaCreatePayload,
  CustomerPersonaUpdatePayload,
} from '@/types/customer/persona';

const MOCK_PERSONA_STORAGE_KEY = 'occacia_customer_personas_mock';

const seedPersonas: CustomerPersona[] = [
  {
    id: 1,
    persona_id: 'persona-sarah',
    customer_id: 'mock-customer-1',
    name: 'Sarah Jenkins',
    relationship: 'Partner',
    birthday: '1994-09-14',
    personality: 'Thoughtful and detail-oriented',
    preferences_json: {
      vibe: ['warm', 'minimal', 'private'],
      favorite_flowers: ['peony', 'orchid'],
    },
    food_preferences: ['Sushi', 'Tasting menus'],
    color_preferences: ['Sage', 'Ivory'],
    music_preferences: ['Jazz', 'Indie soul'],
    personality_tags: ['Calm', 'Creative', 'Romantic'],
    is_confirmed: false,
    confirmed_at: null,
    created_at: new Date(Date.now() - 7 * 86400000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 86400000).toISOString(),
  },
  {
    id: 2,
    persona_id: 'persona-michael',
    customer_id: 'mock-customer-1',
    name: 'Michael Chen',
    relationship: 'Best Friend',
    birthday: '1992-03-03',
    personality: 'Energetic and social',
    preferences_json: {
      dislikes: ['Formal dinners'],
      favorite_themes: ['Games night', 'Outdoor brunch'],
    },
    food_preferences: ['BBQ', 'Comfort food'],
    color_preferences: ['Cobalt', 'Black'],
    music_preferences: ['Electronic', 'Pop'],
    personality_tags: ['Funny', 'Outgoing'],
    is_confirmed: true,
    confirmed_at: new Date(Date.now() - 86400000).toISOString(),
    created_at: new Date(Date.now() - 9 * 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
  },
];

function loadMockPersonas(): CustomerPersona[] {
  if (typeof window === 'undefined') {
    return seedPersonas;
  }

  const stored = localStorage.getItem(MOCK_PERSONA_STORAGE_KEY);
  if (!stored) {
    localStorage.setItem(MOCK_PERSONA_STORAGE_KEY, JSON.stringify(seedPersonas));
    return seedPersonas;
  }

  try {
    return JSON.parse(stored) as CustomerPersona[];
  } catch {
    localStorage.setItem(MOCK_PERSONA_STORAGE_KEY, JSON.stringify(seedPersonas));
    return seedPersonas;
  }
}

function persistMockPersonas(personas: CustomerPersona[]) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(MOCK_PERSONA_STORAGE_KEY, JSON.stringify(personas));
  }
}

export const mockCustomerPersonaService = {
  async listPersonas(): Promise<ServiceResult<CustomerPersona[]>> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    return {
      ok: true,
      status: 200,
      data: loadMockPersonas(),
    };
  },

  async createPersona(payload: CustomerPersonaCreatePayload): Promise<ServiceResult<CustomerPersona>> {
    await new Promise((resolve) => setTimeout(resolve, 150));

    const now = new Date().toISOString();
    const personas = loadMockPersonas();
    const nextPersona: CustomerPersona = {
      id: personas.length ? Math.max(...personas.map((item) => item.id)) + 1 : 1,
      persona_id: `persona-${Date.now()}`,
      customer_id: personas[0]?.customer_id ?? 'mock-customer-1',
      name: payload.name.trim(),
      relationship: payload.relationship ?? null,
      birthday: payload.birthday ?? null,
      personality: payload.personality ?? null,
      preferences_json: payload.preferences_json ?? null,
      food_preferences: payload.food_preferences ?? [],
      color_preferences: payload.color_preferences ?? [],
      music_preferences: payload.music_preferences ?? [],
      personality_tags: payload.personality_tags ?? [],
      is_confirmed: false,
      confirmed_at: null,
      created_at: now,
      updated_at: now,
    };

    const nextPersonas = [nextPersona, ...personas];
    persistMockPersonas(nextPersonas);

    return {
      ok: true,
      status: 201,
      data: nextPersona,
    };
  },

  async getPersona(personaId: string): Promise<ServiceResult<CustomerPersona>> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    const persona = loadMockPersonas().find((item) => item.persona_id === personaId);
    if (!persona) {
      return {
        ok: false,
        status: 404,
        error: 'Persona details were unavailable.',
      };
    }

    return {
      ok: true,
      status: 200,
      data: persona,
    };
  },

  async updatePersona(
    personaId: string,
    payload: CustomerPersonaUpdatePayload
  ): Promise<ServiceResult<CustomerPersona>> {
    await new Promise((resolve) => setTimeout(resolve, 150));

    const personas = loadMockPersonas();
    const index = personas.findIndex((item) => item.persona_id === personaId);

    if (index < 0) {
      return {
        ok: false,
        status: 404,
        error: 'Unable to save persona changes.',
      };
    }

    personas[index] = {
      ...personas[index],
      ...payload,
      updated_at: new Date().toISOString(),
    };
    persistMockPersonas(personas);

    return {
      ok: true,
      status: 200,
      data: personas[index],
    };
  },

  async confirmPersona(personaId: string): Promise<ServiceResult<CustomerPersona | null>> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    const personas = loadMockPersonas();
    const index = personas.findIndex((item) => item.persona_id === personaId);
    if (index < 0) {
      return {
        ok: false,
        status: 404,
        error: 'Unable to confirm persona.',
      };
    }

    personas[index] = {
      ...personas[index],
      is_confirmed: true,
      confirmed_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    persistMockPersonas(personas);

    return {
      ok: true,
      status: 200,
      data: personas[index],
    };
  },

  async unconfirmPersona(personaId: string): Promise<ServiceResult<CustomerPersona | null>> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    const personas = loadMockPersonas();
    const index = personas.findIndex((item) => item.persona_id === personaId);
    if (index < 0) {
      return {
        ok: false,
        status: 404,
        error: 'Unable to remove confirmation.',
      };
    }

    personas[index] = {
      ...personas[index],
      is_confirmed: false,
      confirmed_at: null,
      updated_at: new Date().toISOString(),
    };
    persistMockPersonas(personas);

    return {
      ok: true,
      status: 200,
      data: personas[index],
    };
  },

  async deletePersona(personaId: string): Promise<ServiceResult<void>> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    const personas = loadMockPersonas();
    const nextPersonas = personas.filter((item) => item.persona_id !== personaId);

    if (nextPersonas.length === personas.length) {
      return {
        ok: false,
        status: 404,
        error: 'Unable to delete persona.',
      };
    }

    persistMockPersonas(nextPersonas);

    return {
      ok: true,
      status: 204,
      data: undefined,
    };
  },
};
