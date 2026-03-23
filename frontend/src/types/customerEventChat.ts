export type EventState = 'draft' | 'active';

export type ChatMessageRole = 'assistant' | 'customer' | 'system';

export type ReminderChannel = 'in-app' | 'push' | 'email';

export type CalendarProviderId = 'google' | 'apple' | 'microsoft';

export type RecurrenceFrequency = 'daily' | 'weekly' | 'monthly' | 'yearly';

export type RecurrenceEndType = 'never' | 'until' | 'count';

export type EventTask = {
  id: string;
  title: string;
  description?: string;
  category?: string;
  needsVendor: boolean;
  completed: boolean;
  confirmed: boolean;
  source: 'template' | 'assistant' | 'manual';
  createdAt: string;
};

export type EventChatMessage = {
  id: string;
  role: ChatMessageRole;
  content: string;
  createdAt: string;
};

export type EventSchedule = {
  dateTBD: boolean;
  startAt?: string;
  endAt?: string;
  timezone: string;
  isAllDay: boolean;
  recurrence: {
    isRecurring: boolean;
    frequency?: RecurrenceFrequency;
    interval?: number;
    byDay?: string[];
    endType: RecurrenceEndType;
    until?: string;
    count?: number;
  };
  nextOccurrence?: string;
};

export type EventReminders = {
  enabled: boolean;
  channels: ReminderChannel[];
  offsetsMinutes: number[];
  permissionStatus?: 'granted' | 'denied' | 'default' | 'unsupported';
};

export type CalendarProvider = {
  id: CalendarProviderId;
  label: string;
  connected: boolean;
};

export type CalendarConnectionStatus = {
  connected: boolean;
  provider?: CalendarProviderId;
  accountEmail?: string;
  calendarId?: string;
};

export type EventCalendarSync = {
  enabled: boolean;
  provider?: CalendarProviderId;
  calendarId?: string;
  lastSyncedAt?: string;
};

export type EventSummary = {
  keyDetails: string[];
  scheduleSummary: string;
  reminderSummary: string;
  taskSummary: string;
};

export type CustomerEventDetail = {
  eventId: string;
  title: string;
  description?: string;
  eventType: string;
  state: EventState;
  personaIds: string[];
  schedule: EventSchedule;
  reminders: EventReminders;
  calendarSync: EventCalendarSync;
  updatedAt: string;
};

export type ApiEnvelope<T> = {
  status: 'success' | 'error';
  message: string;
  data?: T;
};

export type EventDetailResponse = ApiEnvelope<{ event: CustomerEventDetail }>;

export type EventMessagesResponse = ApiEnvelope<{ messages: EventChatMessage[] }>;

export type EventTasksResponse = ApiEnvelope<{ tasks: EventTask[] }>;

export type EventTaskMutationPayload = {
  title: string;
  description?: string;
  needsVendor?: boolean;
  category?: string;
};

export type EventTaskResponse = ApiEnvelope<{ task: EventTask }>;

export type EventTasksConfirmResponse = ApiEnvelope<{
  eventState: EventState;
  scheduleSaved: boolean;
  remindersScheduled: boolean;
  calendarSynced: boolean;
}>;

export type EventChatRequest = {
  content: string;
  message?: string;
};

export type EventChatResponse = ApiEnvelope<{
  message: EventChatMessage;
  suggestedTasks?: EventTask[];
  clarification?: string;
}>;

export type EventScheduleRequest = {
  dateTBD?: boolean;
  startAt?: string;
  endAt?: string;
  timezone: string;
  isAllDay: boolean;
  recurrenceRule?: {
    isRecurring: boolean;
    frequency?: RecurrenceFrequency;
    interval?: number;
    byDay?: string[];
    endType?: RecurrenceEndType;
    until?: string;
    count?: number;
  };
};

export type EventScheduleResponse = ApiEnvelope<{
  schedule: EventSchedule;
  clarification?: string;
}>;

export type EventRemindersRequest = {
  enabled: boolean;
  channels: ReminderChannel[];
  offsetsMinutes: number[];
  permissionStatus?: EventReminders['permissionStatus'];
};

export type EventRemindersResponse = ApiEnvelope<{ reminders: EventReminders }>;

export type CalendarProvidersResponse = ApiEnvelope<{ providers: CalendarProvider[] }>;

export type CalendarStatusResponse = ApiEnvelope<{ status: CalendarConnectionStatus }>;

export type CalendarConnectRequest = {
  provider: CalendarProviderId;
  redirectUri?: string;
  scopes?: string[];
};

export type CalendarConnectOauthResponse = {
  provider: string;
  authorizationUrl: string;
  state: string;
};

export type CalendarConnectResponse =
  | ApiEnvelope<{ status: CalendarConnectionStatus }>
  | CalendarConnectOauthResponse;

export type CalendarSyncRequest = {
  enabled: boolean;
  provider?: CalendarProviderId;
  calendarId?: string;
};

export type CalendarSyncResponse = ApiEnvelope<{ calendarSync: EventCalendarSync }>;

export type EventSummaryResponse = ApiEnvelope<{ summary: EventSummary }>;
