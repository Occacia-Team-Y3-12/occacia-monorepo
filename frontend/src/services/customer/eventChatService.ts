import { featureFlags } from '@/config/featureFlags';
import { mockCustomerEventChatService } from '@/mocks/customer/eventChatService';
import { getStoredCustomerToken } from '@/services/customer/authService.shared';
import { handleCustomerFetchUnauthorized } from '@/services/http';
import {
  CalendarConnectionStatus,
  CalendarProvider,
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
  EventTask,
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

const toRruleDate = (value: string) => value.replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');

const buildRecurrenceRule = (payload: EventScheduleRequest): string | undefined => {
  const recurrence = payload.recurrenceRule;
  if (!recurrence?.isRecurring || !recurrence.frequency) {
    return undefined;
  }

  const parts = [`FREQ=${recurrence.frequency.toUpperCase()}`];
  if (recurrence.interval && recurrence.interval > 1) {
    parts.push(`INTERVAL=${recurrence.interval}`);
  }
  if (recurrence.byDay?.length) {
    parts.push(`BYDAY=${recurrence.byDay.join(',')}`);
  }
  if (recurrence.endType === 'until' && recurrence.until) {
    const until = new Date(recurrence.until).toISOString();
    parts.push(`UNTIL=${toRruleDate(until)}`);
  } else if (recurrence.endType === 'count' && recurrence.count && recurrence.count > 0) {
    parts.push(`COUNT=${recurrence.count}`);
  }

  return parts.join(';');
};

const minutesToDuration = (minutes: number): string => {
  if (minutes <= 0) {
    return 'PT0M';
  }
  if (minutes % 1440 === 0) {
    return `P${minutes / 1440}D`;
  }
  if (minutes % 60 === 0) {
    return `PT${minutes / 60}H`;
  }
  return `PT${minutes}M`;
};

const toBackendReminderChannel = (channel: string): string => {
  if (channel === 'in-app') return 'IN_APP';
  return channel.toUpperCase();
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const parseBackendTask = (value: unknown): EventTask | null => {
  if (!isRecord(value)) {
    return null;
  }

  const taskId = typeof value.taskId === 'string' ? value.taskId : null;
  const name = typeof value.name === 'string' ? value.name : null;
  if (!taskId || !name) {
    return null;
  }

  const status = typeof value.status === 'string' ? value.status.toUpperCase() : 'DRAFT';
  const confirmedAt = typeof value.confirmedAt === 'string' ? value.confirmedAt : undefined;
  const createdAt = typeof value.createdAt === 'string' ? value.createdAt : new Date().toISOString();
  const vendorCategory = typeof value.vendorCategory === 'string' ? value.vendorCategory : undefined;

  return {
    id: taskId,
    title: name,
    description: typeof value.description === 'string' ? value.description : undefined,
    category: vendorCategory,
    needsVendor: Boolean(value.needsVendor),
    completed: status === 'COMPLETED',
    confirmed: Boolean(confirmedAt) || status !== 'DRAFT',
    source: 'manual',
    createdAt,
  };
};

const normalizeTasksResponse = (raw: unknown): EventTasksResponse | undefined => {
  if (!isRecord(raw)) {
    return undefined;
  }

  if (
    raw.status === 'success'
    && isRecord(raw.data)
    && Array.isArray(raw.data.tasks)
  ) {
    return raw as EventTasksResponse;
  }

  if (Array.isArray(raw.items)) {
    const tasks = raw.items.map(parseBackendTask).filter((task): task is EventTask => task !== null);
    return {
      status: 'success',
      message: 'Tasks fetched successfully.',
      data: { tasks },
    };
  }

  return undefined;
};

const parseRecurrenceRule = (value?: string) => {
  const fallback = {
    isRecurring: false,
    endType: 'never' as const,
  };
  if (!value) {
    return fallback;
  }

  const parts = value.split(';');
  const map = new Map<string, string>();
  parts.forEach((part) => {
    const [key, val] = part.split('=');
    if (key && val) {
      map.set(key.toUpperCase(), val);
    }
  });

  const frequency = map.get('FREQ');
  const interval = map.get('INTERVAL');
  const byDay = map.get('BYDAY');
  const until = map.get('UNTIL');
  const count = map.get('COUNT');

  return {
    isRecurring: true,
    frequency: frequency?.toLowerCase() as 'daily' | 'weekly' | 'monthly' | 'yearly' | undefined,
    interval: interval ? Number(interval) : undefined,
    byDay: byDay ? byDay.split(',') : undefined,
    endType: until ? 'until' as const : count ? 'count' as const : 'never' as const,
    until: until || undefined,
    count: count ? Number(count) : undefined,
  };
};

const normalizeEventResponse = (raw: unknown): EventDetailResponse | undefined => {
  if (!isRecord(raw)) {
    return undefined;
  }

  if (
    raw.status === 'success'
    && isRecord(raw.data)
    && isRecord(raw.data.event)
  ) {
    return raw as EventDetailResponse;
  }

  if (typeof raw.eventId !== 'string' || typeof raw.title !== 'string') {
    return undefined;
  }

  const recurrence = parseRecurrenceRule(typeof raw.recurrenceRule === 'string' ? raw.recurrenceRule : undefined);
  const reminderChannels = Array.isArray(raw.reminderChannels)
    ? raw.reminderChannels.map((channel) => String(channel).toLowerCase().replace('_', '-'))
    : [];
  const reminderOffsets = Array.isArray(raw.reminderOffsets)
    ? raw.reminderOffsets.map((offset) => String(offset))
    : [];
  const offsetMinutes = reminderOffsets.map((offset) => {
    if (offset.startsWith('P') && offset.endsWith('D')) {
      const days = Number(offset.slice(1, -1));
      return Number.isFinite(days) ? days * 1440 : 0;
    }
    if (offset.startsWith('PT') && offset.endsWith('H')) {
      const hours = Number(offset.slice(2, -1));
      return Number.isFinite(hours) ? hours * 60 : 0;
    }
    if (offset.startsWith('PT') && offset.endsWith('M')) {
      const mins = Number(offset.slice(2, -1));
      return Number.isFinite(mins) ? mins : 0;
    }
    return 0;
  }).filter((value) => value >= 0);

  return {
    status: 'success',
    message: 'Event fetched successfully.',
    data: {
      event: {
        eventId: raw.eventId,
        title: raw.title,
        description: typeof raw.description === 'string' ? raw.description : undefined,
        eventType: typeof raw.eventType === 'string' ? raw.eventType.toLowerCase() : 'others',
        state: typeof raw.status === 'string' && raw.status.toUpperCase() === 'ACTIVE' ? 'active' : 'draft',
        personaIds: Array.isArray(raw.personaIds) ? raw.personaIds.map((id) => String(id)) : [],
        schedule: {
          dateTBD: !raw.startAt,
          startAt: typeof raw.startAt === 'string' ? raw.startAt : undefined,
          endAt: typeof raw.endAt === 'string' ? raw.endAt : undefined,
          timezone: typeof raw.timezone === 'string' ? raw.timezone : 'UTC',
          isAllDay: Boolean(raw.isAllDay),
          recurrence,
        },
        reminders: {
          enabled: Boolean(raw.remindersEnabled),
          channels: reminderChannels as ('in-app' | 'push' | 'email')[],
          offsetsMinutes: offsetMinutes,
          permissionStatus: 'default',
        },
        calendarSync: {
          enabled: typeof raw.calendarSyncState === 'string' && raw.calendarSyncState === 'ENABLED',
          provider: typeof raw.calendarSyncProvider === 'string'
            ? raw.calendarSyncProvider.toLowerCase() as 'google' | 'apple' | 'microsoft'
            : undefined,
          calendarId: typeof raw.calendarSyncCalendarId === 'string' ? raw.calendarSyncCalendarId : undefined,
          lastSyncedAt: typeof raw.calendarLastSyncAt === 'string' ? raw.calendarLastSyncAt : undefined,
        },
        updatedAt: typeof raw.updatedAt === 'string' ? raw.updatedAt : new Date().toISOString(),
      },
    },
  };
};

const normalizeMessagesResponse = (raw: unknown): EventMessagesResponse | undefined => {
  if (!isRecord(raw)) {
    return undefined;
  }

  if (
    raw.status === 'success'
    && isRecord(raw.data)
    && Array.isArray(raw.data.messages)
  ) {
    return raw as EventMessagesResponse;
  }

  if (!Array.isArray(raw.items)) {
    return undefined;
  }

  const messages = raw.items
    .filter(isRecord)
    .map((item) => {
      const sender = typeof item.sender === 'string' ? item.sender.toUpperCase() : 'AI';
      const role: 'customer' | 'assistant' = sender === 'CUSTOMER' ? 'customer' : 'assistant';
      return {
        id: typeof item.messageId === 'string' ? item.messageId : `msg_${Date.now()}`,
        role,
        content: typeof item.content === 'string' ? item.content : '',
        createdAt: typeof item.sentAt === 'string' ? item.sentAt : new Date().toISOString(),
      };
    });

  return {
    status: 'success',
    message: 'Messages fetched successfully.',
    data: { messages },
  };
};

const normalizeCalendarProvidersResponse = (raw: unknown): CalendarProvidersResponse | undefined => {
  if (!isRecord(raw)) {
    return undefined;
  }

  if (
    raw.status === 'success'
    && isRecord(raw.data)
    && Array.isArray(raw.data.providers)
  ) {
    return raw as CalendarProvidersResponse;
  }

  if (!Array.isArray(raw.providers)) {
    return undefined;
  }

  const providers: CalendarProvider[] = raw.providers
    .filter(isRecord)
    .map((provider) => ({
      id: String(provider.type || '').toLowerCase() as CalendarProvider['id'],
      label: typeof provider.displayName === 'string' ? provider.displayName : String(provider.type || ''),
      connected: false,
    }))
    .filter((provider) => Boolean(provider.id));

  return {
    status: 'success',
    message: 'Calendar providers fetched successfully.',
    data: { providers },
  };
};

const normalizeCalendarStatusResponse = (raw: unknown): CalendarStatusResponse | undefined => {
  if (!isRecord(raw)) {
    return undefined;
  }

  if (
    raw.status === 'success'
    && isRecord(raw.data)
    && isRecord(raw.data.status)
  ) {
    return raw as CalendarStatusResponse;
  }

  if (typeof raw.connected !== 'boolean') {
    return undefined;
  }

  const status: CalendarConnectionStatus = {
    connected: raw.connected,
    provider: typeof raw.provider === 'string'
      ? raw.provider.toLowerCase() as CalendarConnectionStatus['provider']
      : undefined,
    calendarId: typeof raw.defaultCalendarId === 'string' ? raw.defaultCalendarId : undefined,
  };

  return {
    status: 'success',
    message: 'Calendar status fetched successfully.',
    data: { status },
  };
};

const normalizeCalendarSyncResponse = (raw: unknown): CalendarSyncResponse | undefined => {
  if (!isRecord(raw)) {
    return undefined;
  }

  if (
    raw.status === 'success'
    && isRecord(raw.data)
    && isRecord(raw.data.calendarSync)
  ) {
    return raw as CalendarSyncResponse;
  }

  if (typeof raw.state !== 'string') {
    return undefined;
  }

  return {
    status: 'success',
    message: 'Calendar sync updated successfully.',
    data: {
      calendarSync: {
        enabled: raw.state === 'ENABLED',
        provider: typeof raw.provider === 'string'
          ? raw.provider.toLowerCase() as 'google' | 'apple' | 'microsoft'
          : undefined,
        calendarId: typeof raw.calendarId === 'string' ? raw.calendarId : undefined,
        lastSyncedAt: typeof raw.lastSyncAt === 'string' ? raw.lastSyncAt : undefined,
      },
    },
  };
};

const normalizeTaskResponse = (raw: unknown, defaultMessage: string): EventTaskResponse | undefined => {
  if (!isRecord(raw)) {
    return undefined;
  }

  if (
    raw.status === 'success'
    && isRecord(raw.data)
    && isRecord(raw.data.task)
  ) {
    return raw as EventTaskResponse;
  }

  const mappedTask = parseBackendTask(raw);
  if (!mappedTask) {
    return undefined;
  }

  return {
    status: 'success',
    message: defaultMessage,
    data: { task: mappedTask },
  };
};

const resolveCalendarRedirectUri = (explicitRedirectUri?: string) => {
  if (explicitRedirectUri?.trim()) {
    return explicitRedirectUri.trim();
  }

  const configuredRedirectUri = process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI?.trim();
  if (configuredRedirectUri) {
    return configuredRedirectUri;
  }

  if (typeof window !== 'undefined') {
    return `${window.location.origin}/oauth/callback`;
  }

  return '';
};

const mapTaskPayloadToBackend = (payload: EventTaskMutationPayload) => {
  const normalizedName = payload.title.trim();
  const normalizedCategory = payload.category?.trim();
  const needsVendor = Boolean(payload.needsVendor);

  return {
    name: normalizedName,
    description: payload.description,
    quantity: 1,
    needsVendor,
    vendorCategory: needsVendor ? normalizedCategory : undefined,
    currency: 'LKR',
  };
};

const mapTaskUpdatePayloadToBackend = (
  payload: Partial<EventTaskMutationPayload> & { completed?: boolean }
) => {
  const normalizedTitle = payload.title?.trim();
  const normalizedCategory = payload.category?.trim();
  const needsVendor = payload.needsVendor;

  return {
    name: normalizedTitle,
    description: payload.description,
    needsVendor,
    vendorCategory: needsVendor ? normalizedCategory : undefined,
    currency: 'LKR',
  };
};

const withCustomerAuthHeaders = (headers?: HeadersInit) => {
  const merged = new Headers(headers);
  const token = getStoredCustomerToken();

  if (token && !merged.has('Authorization')) {
    merged.set('Authorization', `Bearer ${token}`);
  }

  return merged;
};

const request = async <T>(input: RequestInfo | URL, init?: RequestInit): Promise<ServiceResult<T>> => {
  try {
    const response = await fetch(input, {
      ...init,
      headers: withCustomerAuthHeaders(init?.headers),
    });
    if (handleCustomerFetchUnauthorized(response)) {
      return {
        ok: false,
        status: response.status,
        error: 'Unauthorized',
      };
    }
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
    return request<EventDetailResponse>(`/api/v1/customers/events/${eventId}`).then((result) => {
      if (!result.ok) return result;
      const normalized = normalizeEventResponse(result.data);
      if (!normalized) {
        return { ok: false, status: result.status, error: 'Unable to parse event details.' };
      }
      return { ...result, data: normalized };
    });
  },

  getMessages(eventId: string): Promise<ServiceResult<EventMessagesResponse>> {
    return request<EventMessagesResponse>(`/api/v1/customers/events/${eventId}/messages`).then((result) => {
      if (!result.ok) return result;
      const normalized = normalizeMessagesResponse(result.data);
      if (!normalized) {
        return { ok: false, status: result.status, error: 'Unable to parse messages response.' };
      }
      return { ...result, data: normalized };
    });
  },

  postChat(eventId: string, payload: EventChatRequest): Promise<ServiceResult<EventChatResponse>> {
    const content = payload.content?.trim() || payload.message?.trim() || '';

    return request<EventChatResponse>(`/api/v1/customers/events/${eventId}/chat`, {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({ content }),
    });
  },

  getTasks(eventId: string): Promise<ServiceResult<EventTasksResponse>> {
    return request<EventTasksResponse>(`/api/v1/customers/events/${eventId}/tasks`).then((result) => {
      if (!result.ok) {
        return result;
      }

      const normalized = normalizeTasksResponse(result.data);
      if (!normalized) {
        return {
          ok: false,
          status: result.status,
          error: 'Unable to parse tasks response.',
        };
      }

      return {
        ...result,
        data: normalized,
      };
    });
  },

  createTask(eventId: string, payload: EventTaskMutationPayload): Promise<ServiceResult<EventTaskResponse>> {
    const backendPayload = mapTaskPayloadToBackend(payload);

    return request<EventTaskResponse>(`/api/v1/customers/events/${eventId}/tasks`, {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(backendPayload),
    }).then((result) => {
      if (!result.ok) {
        return result;
      }

      const normalized = normalizeTaskResponse(result.data, 'Task created successfully.');
      if (!normalized) {
        return {
          ok: false,
          status: result.status,
          error: 'Unable to parse task response.',
        };
      }

      return {
        ...result,
        data: normalized,
      };
    });
  },

  updateTask(eventId: string, taskId: string, payload: Partial<EventTaskMutationPayload> & { completed?: boolean }): Promise<ServiceResult<EventTaskResponse>> {
    const backendPayload = mapTaskUpdatePayloadToBackend(payload);

    return request<EventTaskResponse>(`/api/v1/customers/events/${eventId}/tasks/${taskId}`, {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify(backendPayload),
    }).then((result) => {
      if (!result.ok) {
        return result;
      }

      const normalized = normalizeTaskResponse(result.data, 'Task updated successfully.');
      if (!normalized) {
        return {
          ok: false,
          status: result.status,
          error: 'Unable to parse task response.',
        };
      }

      return {
        ...result,
        data: normalized,
      };
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
    const recurrenceRule = buildRecurrenceRule(payload);

    return request<EventScheduleResponse>(`/api/v1/customers/events/${eventId}/schedule`, {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify({
        startAt: payload.startAt,
        endAt: payload.endAt,
        timezone: payload.timezone,
        isAllDay: payload.isAllDay,
        recurrenceRule,
        recurrenceUntil:
          payload.recurrenceRule?.endType === 'until' && payload.recurrenceRule?.until
            ? new Date(payload.recurrenceRule.until).toISOString()
            : undefined,
        recurrenceCount:
          payload.recurrenceRule?.endType === 'count'
            ? payload.recurrenceRule?.count
            : undefined,
      }),
    });
  },

  saveReminders(eventId: string, payload: EventRemindersRequest): Promise<ServiceResult<EventRemindersResponse>> {
    return request<EventRemindersResponse>(`/api/v1/customers/events/${eventId}/reminders`, {
      method: 'PUT',
      headers: JSON_HEADERS,
      body: JSON.stringify({
        enabled: payload.enabled,
        channels: payload.channels.map(toBackendReminderChannel),
        offsets: payload.offsetsMinutes.map(minutesToDuration),
      }),
    });
  },

  getCalendarProviders(): Promise<ServiceResult<CalendarProvidersResponse>> {
    return request<CalendarProvidersResponse>('/api/v1/customers/calendar/providers').then((result) => {
      if (!result.ok) return result;
      const normalized = normalizeCalendarProvidersResponse(result.data);
      if (!normalized) {
        return { ok: false, status: result.status, error: 'Unable to parse calendar providers response.' };
      }
      return { ...result, data: normalized };
    });
  },

  getCalendarStatus(): Promise<ServiceResult<CalendarStatusResponse>> {
    return request<CalendarStatusResponse>('/api/v1/customers/calendar/status').then((result) => {
      if (!result.ok) return result;
      const normalized = normalizeCalendarStatusResponse(result.data);
      if (!normalized) {
        return { ok: false, status: result.status, error: 'Unable to parse calendar status response.' };
      }
      return { ...result, data: normalized };
    });
  },

  connectCalendar(payload: CalendarConnectRequest): Promise<ServiceResult<CalendarConnectResponse>> {
    const redirectUri = resolveCalendarRedirectUri(payload.redirectUri);

    return request<CalendarConnectResponse>('/api/v1/customers/calendar/connect', {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify({
        provider: payload.provider,
        redirectUri,
        scopes: payload.scopes ?? [],
      }),
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
      body: JSON.stringify({
        state: payload.enabled ? 'ENABLED' : 'DISABLED',
        provider: payload.provider?.toUpperCase(),
        calendarId: payload.calendarId,
      }),
    }).then((result) => {
      if (!result.ok) return result;
      const normalized = normalizeCalendarSyncResponse(result.data);
      if (!normalized) {
        return { ok: false, status: result.status, error: 'Unable to parse calendar sync response.' };
      }
      return { ...result, data: normalized };
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
