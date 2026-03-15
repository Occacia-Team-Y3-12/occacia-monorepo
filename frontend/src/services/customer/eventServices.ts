import {
  CreateCustomerEventPayload,
  CreateCustomerEventResponse,
  DeleteDraftEventResponse,
  EventTypesResponse,
  ServiceResult,
  UpdateEventPersonasPayload,
  UpdateEventPersonasResponse,
} from '@/types/customer';

const JSON_HEADERS = { 'Content-Type': 'application/json' };

const toErrorMessage = (error: unknown): string => {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return 'Unexpected error occurred.';
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

const parseBody = <T>(raw: string, contentType: string): (T & { message?: string }) | undefined => {
  if (!raw) {
    return undefined;
  }

  if (!contentType.includes('application/json')) {
    return undefined;
  }

  try {
    return JSON.parse(raw) as T & { message?: string };
  } catch {
    return undefined;
  }
};

const request = async <T>(input: RequestInfo | URL, init?: RequestInit): Promise<ServiceResult<T>> => {
  try {
    const response = await fetch(input, init);
    const raw = await response.text();
    const contentType = response.headers.get('content-type') || '';
    const data = parseBody<T>(raw, contentType);
    const fallbackMessage = raw && !contentType.includes('application/json')
      ? raw.slice(0, 180)
      : undefined;

    if (!response.ok) {
      const normalizedMessage = normalizeErrorText(data?.message)
        || normalizeErrorText(fallbackMessage)
        || `Request failed with status ${response.status}.`;

      return {
        ok: false,
        status: response.status,
        data,
        error: normalizedMessage,
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

export const customerEventService = {
  // Fetches available event types and UI examples.
  getEventTypes(): Promise<ServiceResult<EventTypesResponse>> {
    return request<EventTypesResponse>('/api/v1/event-types');
  },

  // Creates an event in draft state and returns its identifier.
  createEvent(payload: CreateCustomerEventPayload): Promise<ServiceResult<CreateCustomerEventResponse>> {
    return request<CreateCustomerEventResponse>('/api/v1/customers/events', {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  // Assigns selected personas to an existing draft event.
  updatePersonas(
    eventId: string,
    payload: UpdateEventPersonasPayload
  ): Promise<ServiceResult<UpdateEventPersonasResponse>> {
    return request<UpdateEventPersonasResponse>(`/api/v1/customers/events/${eventId}/personas`, {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  // Deletes a draft event, used by cancel flow.
  deleteDraft(eventId: string): Promise<ServiceResult<DeleteDraftEventResponse>> {
    return request<DeleteDraftEventResponse>(`/api/v1/customers/events/${eventId}`, {
      method: 'DELETE',
    });
  },
};
