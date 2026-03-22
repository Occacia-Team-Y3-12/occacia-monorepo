import type { ServiceResult } from '@/types/customer';
import type {
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
import { eventStore } from '@/mocks/customer/eventStore';

const success = <T>(status: number, data: T): ServiceResult<T> => ({
  ok: true,
  status,
  data,
});

const failure = <T>(status: number, error: string, data?: T): ServiceResult<T> => ({
  ok: false,
  status,
  error,
  data,
});

const toIso = (value: string, fallbackTime = '00:00'): string => {
  if (value.includes('T')) {
    const normalized = value.endsWith('Z') ? value : `${value}:00`;
    return new Date(normalized).toISOString();
  }
  return new Date(`${value}T${fallbackTime}:00`).toISOString();
};

export const mockCustomerEventChatService = {
  async getEvent(eventId: string): Promise<ServiceResult<EventDetailResponse>> {
    const record = eventStore.ensureEvent(eventId);
    return success(200, {
      status: 'success',
      message: 'Event fetched successfully.',
      data: {
        event: record.event,
      },
    });
  },

  async getMessages(eventId: string): Promise<ServiceResult<EventMessagesResponse>> {
    try {
      const messages = eventStore.getMessages(eventId);
      return success(200, {
        status: 'success',
        message: 'Messages fetched successfully.',
        data: {
          messages,
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch messages.';
      return failure(404, message, {
        status: 'error',
        message,
      });
    }
  },

  async postChat(
    eventId: string,
    payload: EventChatRequest
  ): Promise<ServiceResult<EventChatResponse>> {
    const message = payload.message?.trim();
    if (!message) {
      return failure(400, 'Message is required.', {
        status: 'error',
        message: 'Message is required.',
      });
    }

    try {
      eventStore.addCustomerMessage(eventId, message);
      const assistantMessage = eventStore.addAssistantMessage(eventId, message);
      const tasks = eventStore.getTasks(eventId);

      return success(200, {
        status: 'success',
        message: 'Chat processed successfully.',
        data: {
          message: assistantMessage,
          suggestedTasks: tasks,
        },
      });
    } catch (error) {
      const nextMessage = error instanceof Error ? error.message : 'Failed to process chat.';
      return failure(404, nextMessage, {
        status: 'error',
        message: nextMessage,
      });
    }
  },

  async getTasks(eventId: string): Promise<ServiceResult<EventTasksResponse>> {
    try {
      const tasks = eventStore.getTasks(eventId);
      return success(200, {
        status: 'success',
        message: 'Tasks fetched successfully.',
        data: {
          tasks,
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to fetch tasks.';
      return failure(404, message, {
        status: 'error',
        message,
      });
    }
  },

  async createTask(
    eventId: string,
    payload: EventTaskMutationPayload
  ): Promise<ServiceResult<EventTaskResponse>> {
    const title = payload.title?.trim();
    if (!title) {
      return failure(400, 'Task title is required.', {
        status: 'error',
        message: 'Task title is required.',
      });
    }

    try {
      const task = eventStore.addTask(eventId, {
        ...payload,
        title,
      });
      return success(201, {
        status: 'success',
        message: 'Task created successfully.',
        data: {
          task,
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create task.';
      return failure(404, message, {
        status: 'error',
        message,
      });
    }
  },

  async updateTask(
    eventId: string,
    taskId: string,
    payload: Partial<EventTaskMutationPayload> & { completed?: boolean }
  ): Promise<ServiceResult<EventTaskResponse>> {
    if (typeof payload.title === 'string' && payload.title.trim().length === 0) {
      return failure(400, 'Task title cannot be empty.', {
        status: 'error',
        message: 'Task title cannot be empty.',
      });
    }

    try {
      const task = eventStore.updateTask(eventId, taskId, payload);
      return success(200, {
        status: 'success',
        message: 'Task updated successfully.',
        data: {
          task,
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update task.';
      return failure(404, message, {
        status: 'error',
        message,
      });
    }
  },

  async deleteTask(
    eventId: string,
    taskId: string
  ): Promise<ServiceResult<{ status: 'success' | 'error'; message: string }>> {
    try {
      eventStore.deleteTask(eventId, taskId);
      return success(200, {
        status: 'success',
        message: 'Task deleted successfully.',
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete task.';
      return failure(404, message, {
        status: 'error',
        message,
      });
    }
  },

  async confirmTasks(eventId: string): Promise<ServiceResult<EventTasksConfirmResponse>> {
    try {
      const result = eventStore.confirmTasks(eventId);
      return success(200, {
        status: 'success',
        message: 'Tasks confirmed and event updated successfully.',
        data: result,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to confirm tasks.';
      return failure(400, message, {
        status: 'error',
        message,
      });
    }
  },

  async saveSchedule(
    eventId: string,
    payload: EventScheduleRequest
  ): Promise<ServiceResult<EventScheduleResponse>> {
    try {
      const dateTBD = Boolean(payload.dateTBD);
      const startAt = !dateTBD && payload.startAt ? toIso(payload.startAt, '00:00') : undefined;
      const endAt = !dateTBD && payload.endAt ? toIso(payload.endAt, '23:59') : undefined;

      const schedule = eventStore.saveSchedule(eventId, {
        dateTBD,
        startAt,
        endAt,
        timezone: payload.timezone,
        isAllDay: payload.isAllDay,
        recurrence: {
          isRecurring: Boolean(payload.recurrenceRule?.isRecurring),
          frequency: payload.recurrenceRule?.frequency,
          interval: payload.recurrenceRule?.interval,
          byDay: payload.recurrenceRule?.byDay,
          endType: payload.recurrenceRule?.endType || 'never',
          until: payload.recurrenceRule?.until,
          count: payload.recurrenceRule?.count,
        },
      });

      const clarification =
        schedule.recurrence.isRecurring && schedule.recurrence.frequency === 'yearly'
          ? 'Confirmed yearly recurrence. Keep same date each year?'
          : undefined;

      return success(200, {
        status: 'success',
        message: 'Schedule saved successfully.',
        data: {
          schedule,
          clarification,
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save schedule.';
      return failure(400, message, {
        status: 'error',
        message,
      });
    }
  },

  async saveReminders(
    eventId: string,
    payload: EventRemindersRequest
  ): Promise<ServiceResult<EventRemindersResponse>> {
    try {
      const reminders = eventStore.saveReminders(eventId, {
        enabled: payload.enabled,
        channels: payload.channels,
        offsetsMinutes: payload.offsetsMinutes,
        permissionStatus: payload.permissionStatus,
      });

      return success(200, {
        status: 'success',
        message: 'Reminder settings saved successfully.',
        data: {
          reminders,
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save reminders.';
      return failure(400, message, {
        status: 'error',
        message,
      });
    }
  },

  async getCalendarProviders(): Promise<ServiceResult<CalendarProvidersResponse>> {
    return success(200, {
      status: 'success',
      message: 'Calendar providers fetched successfully.',
      data: {
        providers: eventStore.getCalendarProviders(),
      },
    });
  },

  async getCalendarStatus(): Promise<ServiceResult<CalendarStatusResponse>> {
    return success(200, {
      status: 'success',
      message: 'Calendar status fetched successfully.',
      data: {
        status: eventStore.getCalendarStatus(),
      },
    });
  },

  async connectCalendar(
    payload: CalendarConnectRequest
  ): Promise<ServiceResult<CalendarConnectResponse>> {
    const status = eventStore.connectCalendar(payload.provider);
    return success(200, {
      status: 'success',
      message: 'Calendar connected successfully.',
      data: {
        status,
      },
    });
  },

  async disconnectCalendar(): Promise<ServiceResult<{ status: 'success' | 'error'; message: string }>> {
    eventStore.disconnectCalendar();
    return success(200, {
      status: 'success',
      message: 'Calendar disconnected successfully.',
    });
  },

  async setCalendarSync(
    eventId: string,
    payload: CalendarSyncRequest
  ): Promise<ServiceResult<CalendarSyncResponse>> {
    try {
      const calendarSync = eventStore.setCalendarSync(
        eventId,
        payload.enabled,
        payload.provider,
        payload.calendarId
      );

      return success(200, {
        status: 'success',
        message: 'Calendar sync settings saved successfully.',
        data: {
          calendarSync,
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to save calendar sync settings.';
      return failure(400, message, {
        status: 'error',
        message,
      });
    }
  },

  async summarize(eventId: string): Promise<ServiceResult<EventSummaryResponse>> {
    try {
      const summary = eventStore.summarize(eventId);
      return success(200, {
        status: 'success',
        message: 'Event summary generated successfully.',
        data: {
          summary,
        },
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to generate summary.';
      return failure(400, message, {
        status: 'error',
        message,
      });
    }
  },
};
