import { CreateCustomerEventPayload } from '@/types/customer';
import {
  CalendarConnectionStatus,
  CalendarProvider,
  CalendarProviderId,
  CustomerEventDetail,
  EventChatMessage,
  EventReminders,
  EventSchedule,
  EventTask,
  EventTaskMutationPayload,
} from '@/types/customerEventChat';

type EventRecord = {
  event: CustomerEventDetail;
  tasks: EventTask[];
  messages: EventChatMessage[];
};

type EventStore = {
  events: Record<string, EventRecord>;
  calendarStatus: CalendarConnectionStatus;
};

declare global {
  // eslint-disable-next-line no-var
  var __occaciaEventStore: EventStore | undefined;
}

const now = () => new Date().toISOString();

const defaultSchedule = (): EventSchedule => ({
  dateTBD: true,
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
  isAllDay: true,
  recurrence: {
    isRecurring: false,
    endType: 'never',
  },
});

const defaultReminders = (): EventReminders => ({
  enabled: false,
  channels: ['in-app'],
  offsetsMinutes: [1440],
  permissionStatus: 'default',
});

const taskTemplatesByType: Record<string, string[]> = {
  individual: ['Book venue', 'Order custom flowers', 'Buy gift'],
  group: ['Finalize guest list', 'Book venue', 'Plan group menu'],
  others: ['Set key milestones', 'Confirm logistics', 'Prepare checklist'],
};

const getStore = (): EventStore => {
  if (!globalThis.__occaciaEventStore) {
    globalThis.__occaciaEventStore = {
      events: {},
      calendarStatus: {
        connected: false,
      },
    };
  }
  return globalThis.__occaciaEventStore;
};

const buildTemplateTasks = (eventType: string): EventTask[] => {
  const templates = taskTemplatesByType[eventType] || taskTemplatesByType.others;
  return templates.map((title, index) => ({
    id: `tsk_${Date.now()}_${index}`,
    title,
    description: '',
    category: 'general',
    needsVendor: index < 2,
    completed: false,
    confirmed: false,
    source: 'template',
    createdAt: now(),
  }));
};

const buildInitialMessage = (eventTitle: string): EventChatMessage => ({
  id: `msg_${Date.now()}_assistant_init`,
  role: 'assistant',
  content: `I created a starter plan for ${eventTitle}. When is the event, and should it repeat? Also, tell me your budget and any must-have preferences.`,
  createdAt: now(),
});

const nextOccurrenceFromSchedule = (schedule: EventSchedule): string | undefined => {
  if (schedule.dateTBD || !schedule.startAt) {
    return undefined;
  }

  const start = new Date(schedule.startAt);
  if (Number.isNaN(start.getTime())) {
    return undefined;
  }

  if (!schedule.recurrence.isRecurring || !schedule.recurrence.frequency) {
    return start.toISOString();
  }

  const candidate = new Date(start);
  const today = new Date();
  while (candidate < today) {
    switch (schedule.recurrence.frequency) {
      case 'daily':
        candidate.setDate(candidate.getDate() + (schedule.recurrence.interval || 1));
        break;
      case 'weekly':
        candidate.setDate(candidate.getDate() + 7 * (schedule.recurrence.interval || 1));
        break;
      case 'monthly':
        candidate.setMonth(candidate.getMonth() + (schedule.recurrence.interval || 1));
        break;
      case 'yearly':
        candidate.setFullYear(candidate.getFullYear() + (schedule.recurrence.interval || 1));
        break;
      default:
        break;
    }
  }

  return candidate.toISOString();
};

const isIsoDate = (value: string | undefined): boolean => {
  if (!value) {
    return false;
  }
  const dt = new Date(value);
  return !Number.isNaN(dt.getTime());
};

const hasTaskAtLeastOne = (tasks: EventTask[]): boolean => tasks.length > 0;

const deriveAssistantResponse = (message: string, eventType: string): string => {
  const lower = message.toLowerCase();

  if (lower.includes('birthday') || lower.includes('anniversary')) {
    return 'Noted. This sounds recurring yearly. Do you want reminders 7 days and 1 day before?';
  }

  if (lower.includes('budget')) {
    return 'Budget captured. I will prioritize tasks and recommendations to fit your budget range.';
  }

  if (lower.includes('calendar')) {
    return 'If you choose external sync, I can prepare Google, Apple, or Microsoft calendar connection next.';
  }

  if (eventType === 'group') {
    return 'Got it. For group events, I recommend confirming venue, invite flow, and catering deadlines first.';
  }

  return 'Thanks. I captured that detail. Next, share date/time, timezone, recurrence, and reminder preference so I can finalize your plan.';
};

export const eventStore = {
  listEvents(params?: {
    status?: string | null;
    limit?: number;
    cursor?: string | null;
  }) {
    const items = Object.values(getStore().events)
      .filter((record) =>
        params?.status
          ? record.event.state.toLowerCase() === params.status.toLowerCase()
          : true
      )
      .sort((left, right) =>
        right.event.updatedAt.localeCompare(left.event.updatedAt)
      );

    const startIndex = params?.cursor
      ? Math.max(
          0,
          items.findIndex((record) => record.event.eventId === params.cursor) + 1
        )
      : 0;
    const limit = params?.limit ?? 20;
    const pageItems = items.slice(startIndex, startIndex + limit);
    const nextCursor =
      startIndex + limit < items.length
        ? pageItems[pageItems.length - 1]?.event.eventId ?? null
        : null;

    return {
      items: pageItems.map(({ event }) => ({
        eventId: event.eventId,
        customerId: 'mock-customer-1',
        eventType: event.eventType,
        title: event.title,
        description: event.description ?? null,
        locationText: null,
        startAt: event.schedule.startAt ?? null,
        endAt: event.schedule.endAt ?? null,
        timezone: event.schedule.timezone ?? null,
        isAllDay: event.schedule.isAllDay,
        status: event.state,
        personaIds: event.personaIds,
        createdAt: event.updatedAt,
        updatedAt: event.updatedAt,
      })),
      nextCursor,
    };
  },

  createEventWithId(eventId: string, payload: CreateCustomerEventPayload): CustomerEventDetail {
    const store = getStore();

    const event: CustomerEventDetail = {
      eventId,
      title: payload.title.trim(),
      description: payload.description?.trim(),
      eventType: payload.eventType,
      state: 'draft',
      personaIds: [],
      schedule: defaultSchedule(),
      reminders: defaultReminders(),
      calendarSync: {
        enabled: false,
      },
      updatedAt: now(),
    };

    store.events[eventId] = {
      event,
      tasks: buildTemplateTasks(payload.eventType),
      messages: [buildInitialMessage(event.title)],
    };

    return event;
  },

  createEvent(payload: CreateCustomerEventPayload): CustomerEventDetail {
    const eventId = `evt_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
    return this.createEventWithId(eventId, payload);
  },

  getEvent(eventId: string): EventRecord | undefined {
    return getStore().events[eventId];
  },

  ensureEvent(eventId: string): EventRecord {
    const record = this.getEvent(eventId);
    if (record) {
      return record;
    }

    const fallbackEvent = this.createEventWithId(eventId, {
      eventType: 'others',
      title: 'Event',
    });

    const nextRecord = this.getEvent(eventId);
    if (!nextRecord) {
      throw new Error(`Unable to initialize event ${fallbackEvent.eventId}.`);
    }

    return nextRecord;
  },

  deleteDraft(eventId: string): boolean {
    const store = getStore();
    const record = store.events[eventId];
    if (!record) {
      return false;
    }
    if (record.event.state !== 'draft') {
      return false;
    }
    delete store.events[eventId];
    return true;
  },

  updatePersonas(eventId: string, personaIds: string[]): CustomerEventDetail {
    const record = this.ensureEvent(eventId);
    record.event.personaIds = personaIds;
    record.event.updatedAt = now();
    return record.event;
  },

  getMessages(eventId: string): EventChatMessage[] {
    const record = this.ensureEvent(eventId);
    return record.messages;
  },

  addCustomerMessage(eventId: string, message: string): EventChatMessage {
    const record = this.ensureEvent(eventId);
    const nextMessage: EventChatMessage = {
      id: `msg_${Date.now()}_customer`,
      role: 'customer',
      content: message,
      createdAt: now(),
    };

    record.messages.push(nextMessage);
    record.event.updatedAt = now();
    return nextMessage;
  },

  addAssistantMessage(eventId: string, sourceMessage: string): EventChatMessage {
    const record = this.ensureEvent(eventId);
    const assistantMessage: EventChatMessage = {
      id: `msg_${Date.now()}_assistant`,
      role: 'assistant',
      content: deriveAssistantResponse(sourceMessage, record.event.eventType),
      createdAt: now(),
    };

    record.messages.push(assistantMessage);
    record.event.updatedAt = now();
    return assistantMessage;
  },

  getTasks(eventId: string): EventTask[] {
    const record = this.ensureEvent(eventId);
    return record.tasks;
  },

  addTask(eventId: string, payload: EventTaskMutationPayload): EventTask {
    const record = this.ensureEvent(eventId);
    const task: EventTask = {
      id: `tsk_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      title: payload.title.trim(),
      description: payload.description?.trim(),
      category: payload.category || 'general',
      needsVendor: Boolean(payload.needsVendor),
      completed: false,
      confirmed: false,
      source: 'manual',
      createdAt: now(),
    };

    record.tasks.push(task);
    record.event.updatedAt = now();
    return task;
  },

  updateTask(
    eventId: string,
    taskId: string,
    payload: Partial<EventTaskMutationPayload> & { completed?: boolean }
  ): EventTask {
    const record = this.ensureEvent(eventId);
    const task = record.tasks.find((item) => item.id === taskId);

    if (!task) {
      throw new Error('Task not found.');
    }

    if (typeof payload.title === 'string') {
      task.title = payload.title.trim();
    }

    if (typeof payload.description === 'string') {
      task.description = payload.description.trim();
    }

    if (typeof payload.category === 'string') {
      task.category = payload.category;
    }

    if (typeof payload.needsVendor === 'boolean') {
      task.needsVendor = payload.needsVendor;
    }

    if (typeof payload.completed === 'boolean') {
      task.completed = payload.completed;
    }

    record.event.updatedAt = now();
    return task;
  },

  deleteTask(eventId: string, taskId: string): void {
    const record = this.ensureEvent(eventId);
    const next = record.tasks.filter((item) => item.id !== taskId);

    if (next.length === record.tasks.length) {
      throw new Error('Task not found.');
    }

    record.tasks = next;
    record.event.updatedAt = now();
  },

  saveSchedule(eventId: string, schedule: EventSchedule): EventSchedule {
    if (!schedule.dateTBD && !isIsoDate(schedule.startAt)) {
      throw new Error('Invalid start date/time.');
    }

    if (!schedule.dateTBD && schedule.endAt && !isIsoDate(schedule.endAt)) {
      throw new Error('Invalid end date/time.');
    }

    if (!schedule.timezone) {
      throw new Error('Timezone is required.');
    }

    if (schedule.recurrence.isRecurring) {
      if (!schedule.recurrence.frequency) {
        throw new Error('Recurrence frequency is required for recurring schedules.');
      }

      if (schedule.recurrence.endType === 'until' && !isIsoDate(schedule.recurrence.until)) {
        throw new Error('Recurrence end date is required and must be valid.');
      }

      if (schedule.recurrence.endType === 'count') {
        const count = schedule.recurrence.count || 0;
        if (count < 1 || count > 999) {
          throw new Error('Recurrence count must be between 1 and 999.');
        }
      }
    }

    const record = this.ensureEvent(eventId);
    const nextSchedule = {
      ...schedule,
      nextOccurrence: nextOccurrenceFromSchedule(schedule),
    };

    record.event.schedule = nextSchedule;
    record.event.updatedAt = now();
    return nextSchedule;
  },

  saveReminders(eventId: string, reminders: EventReminders): EventReminders {
    if (reminders.enabled && reminders.offsetsMinutes.length === 0) {
      throw new Error('At least one reminder offset is required when reminders are enabled.');
    }

    if (reminders.offsetsMinutes.some((offset) => offset < 0)) {
      throw new Error('Reminder offsets must be positive values.');
    }

    const uniqueOffsets = Array.from(new Set(reminders.offsetsMinutes)).sort((a, b) => b - a);

    const record = this.ensureEvent(eventId);
    const nextReminders = {
      ...reminders,
      offsetsMinutes: uniqueOffsets,
    };

    record.event.reminders = nextReminders;
    record.event.updatedAt = now();
    return nextReminders;
  },

  getCalendarProviders(): CalendarProvider[] {
    const store = getStore();
    const connectedProvider = store.calendarStatus.provider;

    return [
      { id: 'google', label: 'Google Calendar', connected: connectedProvider === 'google' },
      { id: 'apple', label: 'Apple Calendar', connected: connectedProvider === 'apple' },
      { id: 'microsoft', label: 'Microsoft Outlook', connected: connectedProvider === 'microsoft' },
    ];
  },

  getCalendarStatus(): CalendarConnectionStatus {
    return getStore().calendarStatus;
  },

  connectCalendar(provider: CalendarProviderId): CalendarConnectionStatus {
    const store = getStore();
    store.calendarStatus = {
      connected: true,
      provider,
      accountEmail: 'alex.rivers@example.com',
      calendarId: `${provider}_default_calendar`,
    };

    return store.calendarStatus;
  },

  disconnectCalendar(): void {
    const store = getStore();
    store.calendarStatus = {
      connected: false,
    };
  },

  setCalendarSync(eventId: string, enabled: boolean, provider?: CalendarProviderId, calendarId?: string) {
    const record = this.ensureEvent(eventId);
    const status = this.getCalendarStatus();

    if (enabled && !status.connected) {
      throw new Error('Calendar is not connected. Connect a provider first.');
    }

    record.event.calendarSync = {
      enabled,
      provider: enabled ? provider || status.provider : undefined,
      calendarId: enabled ? calendarId || status.calendarId : undefined,
      lastSyncedAt: enabled ? now() : undefined,
    };

    record.event.updatedAt = now();
    return record.event.calendarSync;
  },

  summarize(eventId: string) {
    const record = this.ensureEvent(eventId);
    const { event, tasks } = record;

    const scheduleSummary = event.schedule.dateTBD
      ? 'Schedule is still TBD.'
      : `${event.schedule.isAllDay ? 'All-day' : 'Timed'} event on ${event.schedule.startAt || 'N/A'} (${event.schedule.timezone}).`;

    const reminderSummary = !event.reminders.enabled
      ? 'Reminders are disabled.'
      : `Reminders via ${event.reminders.channels.join(', ')} at offsets ${event.reminders.offsetsMinutes.join(', ')} minutes.`;

    const confirmedCount = tasks.filter((task) => task.confirmed).length;

    return {
      keyDetails: [
        `Event type: ${event.eventType}`,
        `State: ${event.state}`,
        `Personas: ${event.personaIds.length}`,
      ],
      scheduleSummary,
      reminderSummary,
      taskSummary: `${tasks.length} proposed tasks, ${confirmedCount} confirmed.`,
    };
  },

  confirmTasks(eventId: string) {
    const record = this.ensureEvent(eventId);

    if (!hasTaskAtLeastOne(record.tasks)) {
      throw new Error('Add at least 1 task before confirming.');
    }

    record.tasks = record.tasks.map((task) => ({ ...task, confirmed: true }));

    if (record.event.state === 'draft') {
      record.event.state = 'active';
    }

    record.event.updatedAt = now();

    return {
      eventState: record.event.state,
      scheduleSaved: true,
      remindersScheduled: record.event.reminders.enabled,
      calendarSynced: record.event.calendarSync.enabled,
    };
  },
};
