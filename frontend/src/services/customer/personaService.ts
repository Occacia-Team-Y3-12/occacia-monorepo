import { featureFlags } from '@/config/featureFlags';
import { mockCustomerPersonaService } from '@/mocks/customer/personaService';
import { ServiceResult } from '@/types/customer';
import {
  CustomerPersona,
  CustomerPersonaCreatePayload,
  CustomerPersonaUpdatePayload,
} from '@/types/customer/persona';

type CustomerPersonaService = {
  listPersonas(): Promise<ServiceResult<CustomerPersona[]>>;
  createPersona(payload: CustomerPersonaCreatePayload): Promise<ServiceResult<CustomerPersona>>;
  getPersona(personaId: string): Promise<ServiceResult<CustomerPersona>>;
  updatePersona(
    personaId: string,
    payload: CustomerPersonaUpdatePayload
  ): Promise<ServiceResult<CustomerPersona>>;
  confirmPersona(personaId: string): Promise<ServiceResult<CustomerPersona | null>>;
  unconfirmPersona(personaId: string): Promise<ServiceResult<CustomerPersona | null>>;
  deletePersona(personaId: string): Promise<ServiceResult<void>>;
};

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

const apiCustomerPersonaService: CustomerPersonaService = {
  async listPersonas(): Promise<ServiceResult<CustomerPersona[]>> {
    const result = await request('/api/v1/customers/personas/');
    return {
      ...result,
      data: extractPersonaList(result.data) ?? [],
      error: result.ok ? undefined : result.error,
    };
  },

  async createPersona(payload: CustomerPersonaCreatePayload): Promise<ServiceResult<CustomerPersona>> {
    const result = await request('/api/v1/customers/personas/', {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });

    return {
      ...result,
      data: extractPersona(result.data) ?? undefined,
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

  async deletePersona(personaId: string): Promise<ServiceResult<void>> {
    const result = await request(`/api/v1/customers/personas/${personaId}`, {
      method: 'DELETE',
    });

    return {
      ...result,
      data: undefined,
    };
  },
};

export const customerPersonaService: CustomerPersonaService = featureFlags.useCustomerPersonaMock
  ? mockCustomerPersonaService
  : apiCustomerPersonaService;
