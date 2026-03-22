import { featureFlags } from '@/config/featureFlags';
import { mockCustomerEventChatService } from '@/mocks/customer/eventChatService';
import {
  CalendarConnectRequest,
  CalendarConnectResponse,
  CalendarProvidersResponse,
  CalendarStatusResponse,
  CalendarSyncRequest,
  CalendarSyncResponse,
  EventChatRequest,
  EventChatResponse,
  EventDetailResponse,
  EventMessagesResponse,
  EventRemindersRequest,
  EventRemindersResponse,
  EventScheduleRequest,
  EventScheduleResponse,
  EventSummaryResponse,
  EventTaskMutationPayload,
  EventTaskResponse,
  EventTasksConfirmResponse,
  EventTasksResponse,
} from '@/types/customerEventChat';
import { ServiceResult } from '@/types/customer';

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

export type CustomerEventChatService = {
  getEvent(eventId: string): Promise<ServiceResult<EventDetailResponse>>;
  getMessages(eventId: string): Promise<ServiceResult<EventMessagesResponse>>;
  postChat(eventId: string, payload: EventChatRequest): Promise<ServiceResult<EventChatResponse>>;
  getTasks(eventId: string): Promise<ServiceResult<EventTasksResponse>>;
  createTask(eventId: string, payload: EventTaskMutationPayload): Promise<ServiceResult<EventTaskResponse>>;
  updateTask(eventId: string, taskId: string, payload: Partial<EventTaskMutationPayload> & { completed?: boolean }): Promise<ServiceResult<EventTaskResponse>>;
  deleteTask(eventId: string, taskId: string): Promise<ServiceResult<{ status: 'success' | 'error'; message: string }>>;
  confirmTasks(eventId: string): Promise<ServiceResult<EventTasksConfirmResponse>>;
  saveSchedule(eventId: string, payload: EventScheduleRequest): Promise<ServiceResult<EventScheduleResponse>>;
  saveReminders(eventId: string, payload: EventRemindersRequest): Promise<ServiceResult<EventRemindersResponse>>;
  getCalendarProviders(): Promise<ServiceResult<CalendarProvidersResponse>>;
  getCalendarStatus(): Promise<ServiceResult<CalendarStatusResponse>>;
  connectCalendar(payload: CalendarConnectRequest): Promise<ServiceResult<CalendarConnectResponse>>;
  disconnectCalendar(): Promise<ServiceResult<{ status: 'success' | 'error'; message: string }>>;
  setCalendarSync(eventId: string, payload: CalendarSyncRequest): Promise<ServiceResult<CalendarSyncResponse>>;
  summarize(eventId: string): Promise<ServiceResult<EventSummaryResponse>>;
};

const apiCustomerEventChatService: CustomerEventChatService = {
  getEvent(eventId: string): Promise<ServiceResult<EventDetailResponse>> {
    return request<EventDetailResponse>(`/api/v1/customers/events/${eventId}`);
  },

  getMessages(eventId: string): Promise<ServiceResult<EventMessagesResponse>> {
    return request<EventMessagesResponse>(`/api/v1/customers/events/${eventId}/messages`);
  },

  postChat(eventId: string, payload: EventChatRequest): Promise<ServiceResult<EventChatResponse>> {
    return request<EventChatResponse>(`/api/v1/customers/events/${eventId}/chat`, {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  getTasks(eventId: string): Promise<ServiceResult<EventTasksResponse>> {
    return request<EventTasksResponse>(`/api/v1/customers/events/${eventId}/tasks`);
  },

  createTask(eventId: string, payload: EventTaskMutationPayload): Promise<ServiceResult<EventTaskResponse>> {
    return request<EventTaskResponse>(`/api/v1/customers/events/${eventId}/tasks`, {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  updateTask(eventId: string, taskId: string, payload: Partial<EventTaskMutationPayload> & { completed?: boolean }): Promise<ServiceResult<EventTaskResponse>> {
    return request<EventTaskResponse>(`/api/v1/customers/events/${eventId}/tasks/${taskId}`, {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  deleteTask(eventId: string, taskId: string): Promise<ServiceResult<{ status: 'success' | 'error'; message: string }>> {
    return request<{ status: 'success' | 'error'; message: string }>(`/api/v1/customers/events/${eventId}/tasks/${taskId}`, {
      method: 'DELETE',
    });
  },

  confirmTasks(eventId: string): Promise<ServiceResult<EventTasksConfirmResponse>> {
    return request<EventTasksConfirmResponse>(`/api/v1/customers/events/${eventId}/tasks/confirm`, {
      method: 'POST',
    });
  },

  saveSchedule(eventId: string, payload: EventScheduleRequest): Promise<ServiceResult<EventScheduleResponse>> {
    return request<EventScheduleResponse>(`/api/v1/customers/events/${eventId}/schedule`, {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  saveReminders(eventId: string, payload: EventRemindersRequest): Promise<ServiceResult<EventRemindersResponse>> {
    return request<EventRemindersResponse>(`/api/v1/customers/events/${eventId}/reminders`, {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  getCalendarProviders(): Promise<ServiceResult<CalendarProvidersResponse>> {
    return request<CalendarProvidersResponse>('/api/v1/customers/calendar/providers');
  },

  getCalendarStatus(): Promise<ServiceResult<CalendarStatusResponse>> {
    return request<CalendarStatusResponse>('/api/v1/customers/calendar/status');
  },

  connectCalendar(payload: CalendarConnectRequest): Promise<ServiceResult<CalendarConnectResponse>> {
    return request<CalendarConnectResponse>('/api/v1/customers/calendar/connect', {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  disconnectCalendar(): Promise<ServiceResult<{ status: 'success' | 'error'; message: string }>> {
    return request<{ status: 'success' | 'error'; message: string }>('/api/v1/customers/calendar/disconnect', {
      method: 'DELETE',
    });
  },

  setCalendarSync(eventId: string, payload: CalendarSyncRequest): Promise<ServiceResult<CalendarSyncResponse>> {
    return request<CalendarSyncResponse>(`/api/v1/customers/events/${eventId}/calendar-sync`, {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  summarize(eventId: string): Promise<ServiceResult<EventSummaryResponse>> {
    return request<EventSummaryResponse>(`/api/v1/customers/events/${eventId}/summarize`, {
      method: 'POST',
    });
  },
};

export const customerEventChatService: CustomerEventChatService =
  featureFlags.useCustomerPlanningMockApi
    ? mockCustomerEventChatService
    : apiCustomerEventChatService;
