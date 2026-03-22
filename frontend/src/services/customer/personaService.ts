import { featureFlags } from '@/config/featureFlags';
import { ServiceResult } from '@/types/customer';
import {
  CustomerPersona,
  CustomerPersonaUpdatePayload,
} from '@/types/customer/persona';

const JSON_HEADERS = { 'Content-Type': 'application/json' };

const toErrorMessage = (error: unknown): string => {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return 'Unexpected error occurred.';
};

const parseBody = (raw: string, contentType: string): unknown => {
  if (!raw || !contentType.includes('application/json')) {
    return undefined;
  }

  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return undefined;
  }
};

const normalizeErrorText = (value?: string): string | undefined => {
  if (!value) {
    return undefined;
  }

  const trimmed = value.trim();
  const lowered = trimmed.toLowerCase();
  if (lowered === 'internal server error' || lowered.includes('internal server error')) {
    return 'Something went wrong. Please try again.';
  }

  return trimmed;
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const extractMessage = (value: unknown): string | undefined => {
  if (!isRecord(value)) {
    return undefined;
  }

  const message = value.message;
  return typeof message === 'string' ? normalizeErrorText(message) : undefined;
};

const request = async (input: RequestInfo | URL, init?: RequestInit): Promise<ServiceResult<unknown>> => {
  try {
    const response = await fetch(input, init);
    const raw = await response.text();
    const contentType = response.headers.get('content-type') || '';
    const data = parseBody(raw, contentType);
    const fallbackMessage = raw && !contentType.includes('application/json')
      ? raw.slice(0, 180)
      : undefined;

    if (!response.ok) {
      const message = extractMessage(data)
        || normalizeErrorText(fallbackMessage)
        || `Request failed with status ${response.status}.`;

      return {
        ok: false,
        status: response.status,
        data,
        error: message,
      };
    }

    return {
      ok: true,
      status: response.status,
      data,
    };
  } catch (error) {
    return {
      ok: false,
      status: 500,
      error: toErrorMessage(error),
    };
  }
};

const isPersona = (value: unknown): value is CustomerPersona => (
  isRecord(value)
  && typeof value.id === 'number'
  && typeof value.persona_id === 'string'
  && typeof value.name === 'string'
);

const extractPersonaList = (value: unknown): CustomerPersona[] | undefined => {
  if (Array.isArray(value) && value.every(isPersona)) {
    return value;
  }

  if (!isRecord(value)) {
    return undefined;
  }

  const directData = value.data;
  if (Array.isArray(directData) && directData.every(isPersona)) {
    return directData;
  }

  const personas = value.personas;
  if (Array.isArray(personas) && personas.every(isPersona)) {
    return personas;
  }

  if (isRecord(directData)) {
    const nestedPersonas = directData.personas;
    if (Array.isArray(nestedPersonas) && nestedPersonas.every(isPersona)) {
      return nestedPersonas;
    }
  }

  return undefined;
};

const extractPersona = (value: unknown): CustomerPersona | null | undefined => {
  if (isPersona(value)) {
    return value;
  }

  if (value === null) {
    return null;
  }

  if (!isRecord(value)) {
    return undefined;
  }

  const directData = value.data;
  if (isPersona(directData)) {
    return directData;
  }

  const persona = value.persona;
  if (isPersona(persona)) {
    return persona;
  }

  if (isRecord(directData) && isPersona(directData.persona)) {
    return directData.persona;
  }

  return undefined;
};

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

const apiCustomerPersonaService = {
  async listPersonas(): Promise<ServiceResult<CustomerPersona[]>> {
    const result = await request('/api/v1/customers/personas/');
    return {
      ...result,
      data: extractPersonaList(result.data) ?? [],
      error: result.ok ? undefined : result.error,
    };
  },

  async getPersona(personaId: string): Promise<ServiceResult<CustomerPersona>> {
    const result = await request(`/api/v1/customers/personas/${personaId}`);
    const persona = extractPersona(result.data);

    if (result.ok && !persona) {
      return {
        ok: false,
        status: result.status,
        error: 'Persona details were unavailable.',
      };
    }

    return {
      ...result,
      data: persona ?? undefined,
    };
  },

  async updatePersona(
    personaId: string,
    payload: CustomerPersonaUpdatePayload
  ): Promise<ServiceResult<CustomerPersona>> {
    const result = await request(`/api/v1/customers/personas/${personaId}`, {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });

    return {
      ...result,
      data: extractPersona(result.data) ?? undefined,
    };
  },

  async confirmPersona(personaId: string): Promise<ServiceResult<CustomerPersona | null>> {
    const result = await request(`/api/v1/customers/personas/${personaId}/confirm`, {
      method: 'POST',
    });

    return {
      ...result,
      data: extractPersona(result.data),
    };
  },

  async unconfirmPersona(personaId: string): Promise<ServiceResult<CustomerPersona | null>> {
    const result = await request(`/api/v1/customers/personas/${personaId}/confirm`, {
      method: 'DELETE',
    });

    return {
      ...result,
      data: extractPersona(result.data),
    };
  },
};

const mockCustomerPersonaService = {
  async listPersonas(): Promise<ServiceResult<CustomerPersona[]>> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    return {
      ok: true,
      status: 200,
      data: loadMockPersonas(),
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
};

export const customerPersonaService = featureFlags.useCustomerPersonaMock
  ? mockCustomerPersonaService
  : apiCustomerPersonaService;
