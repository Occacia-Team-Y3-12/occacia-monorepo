'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { customerEventChatService } from '@/services/customer/eventChatService';
import {
  CalendarConnectionStatus,
  CalendarProvider,
  CalendarProviderId,
  EventChatMessage,
  EventSummary,
  EventTask,
  ReminderChannel,
  RecurrenceEndType,
  RecurrenceFrequency,
} from '@/types/customerEventChat';

const DEFAULT_TIMEZONE = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
const DEFAULT_OFFSETS = [10080, 1440, 60];
const GENERIC_ERROR_TEXT = 'Something went wrong. Please try again.';

const toLocalDate = (iso?: string): string => {
  if (!iso) {
    return '';
  }
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) {
    return '';
  }
  return dt.toISOString().slice(0, 10);
};

const toLocalTime = (iso?: string): string => {
  if (!iso) {
    return '09:00';
  }
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) {
    return '09:00';
  }
  return `${String(dt.getHours()).padStart(2, '0')}:${String(dt.getMinutes()).padStart(2, '0')}`;
};

export const useEventChatPlanner = (eventId: string) => {
  const router = useRouter();

  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [eventTitle, setEventTitle] = useState('Event');
  const [eventState, setEventState] = useState<'draft' | 'active'>('draft');
  const [eventType, setEventType] = useState('others');
  const [personaCount, setPersonaCount] = useState(0);

  const [messages, setMessages] = useState<EventChatMessage[]>([]);
  const [tasks, setTasks] = useState<EventTask[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [newTaskTitle, setNewTaskTitle] = useState('');

  const [dateTBD, setDateTBD] = useState(true);
  const [startDate, setStartDate] = useState('');
  const [startTime, setStartTime] = useState('09:00');
  const [endDate, setEndDate] = useState('');
  const [endTime, setEndTime] = useState('10:00');
  const [timezone, setTimezone] = useState(DEFAULT_TIMEZONE);
  const [isAllDay, setIsAllDay] = useState(true);

  const [isRecurring, setIsRecurring] = useState(false);
  const [frequency, setFrequency] = useState<RecurrenceFrequency>('yearly');
  const [endType, setEndType] = useState<RecurrenceEndType>('never');
  const [recurrenceUntil, setRecurrenceUntil] = useState('');
  const [recurrenceCount, setRecurrenceCount] = useState(1);

  const [remindersEnabled, setRemindersEnabled] = useState(false);
  const [offsets, setOffsets] = useState<number[]>(DEFAULT_OFFSETS);
  const [channels, setChannels] = useState<ReminderChannel[]>(['in-app']);
  const [permissionStatus, setPermissionStatus] = useState<'granted' | 'denied' | 'default' | 'unsupported'>('default');

  const [calendarProviders, setCalendarProviders] = useState<CalendarProvider[]>([]);
  const [calendarStatus, setCalendarStatus] = useState<CalendarConnectionStatus>({ connected: false });
  const [selectedProvider, setSelectedProvider] = useState<CalendarProviderId>('google');
  const [calendarSyncEnabled, setCalendarSyncEnabled] = useState(false);

  const [summary, setSummary] = useState<EventSummary | null>(null);

  const activeTaskCount = useMemo(() => tasks.length, [tasks]);

  const fetchAll = useCallback(async () => {
    setIsInitialLoading(true);
    setError(null);

    const [eventResult, messagesResult, tasksResult, providersResult, calendarStatusResult] = await Promise.all([
      customerEventChatService.getEvent(eventId),
      customerEventChatService.getMessages(eventId),
      customerEventChatService.getTasks(eventId),
      customerEventChatService.getCalendarProviders(),
      customerEventChatService.getCalendarStatus(),
    ]);

    if (eventResult.ok && eventResult.data?.data?.event) {
      const event = eventResult.data.data.event;
      setEventTitle(event.title);
      setEventState(event.state);
      setEventType(event.eventType);
      setPersonaCount(event.personaIds.length);

      setDateTBD(event.schedule.dateTBD);
      setStartDate(toLocalDate(event.schedule.startAt));
      setStartTime(toLocalTime(event.schedule.startAt));
      setEndDate(toLocalDate(event.schedule.endAt));
      setEndTime(toLocalTime(event.schedule.endAt));
      setTimezone(event.schedule.timezone || DEFAULT_TIMEZONE);
      setIsAllDay(event.schedule.isAllDay);

      setIsRecurring(event.schedule.recurrence.isRecurring);
      setFrequency(event.schedule.recurrence.frequency || 'yearly');
      setEndType(event.schedule.recurrence.endType || 'never');
      setRecurrenceUntil(toLocalDate(event.schedule.recurrence.until));
      setRecurrenceCount(event.schedule.recurrence.count || 1);

      setRemindersEnabled(event.reminders.enabled);
      setOffsets(event.reminders.offsetsMinutes.length ? event.reminders.offsetsMinutes : DEFAULT_OFFSETS);
      setChannels(event.reminders.channels.length ? event.reminders.channels : ['in-app']);
      setPermissionStatus(event.reminders.permissionStatus || 'default');

      setCalendarSyncEnabled(event.calendarSync.enabled);
      setSelectedProvider(event.calendarSync.provider || 'google');
    }

    if (messagesResult.ok && messagesResult.data?.data?.messages) {
      setMessages(messagesResult.data.data.messages);
    }

    if (tasksResult.ok && tasksResult.data?.data?.tasks) {
      setTasks(tasksResult.data.data.tasks);
    }

    if (providersResult.ok && providersResult.data?.data?.providers) {
      setCalendarProviders(providersResult.data.data.providers);
    }

    if (calendarStatusResult.ok && calendarStatusResult.data?.data?.status) {
      setCalendarStatus(calendarStatusResult.data.data.status);
      if (calendarStatusResult.data.data.status.provider) {
        setSelectedProvider(calendarStatusResult.data.data.status.provider);
      }
    }

    setIsInitialLoading(false);
  }, [eventId]);

  useEffect(() => {
    void fetchAll();
  }, [fetchAll]);

  const requestNotificationPermission = async (): Promise<typeof permissionStatus> => {
    if (typeof window === 'undefined' || !('Notification' in window)) {
      return 'unsupported';
    }

    if (Notification.permission === 'granted') {
      return 'granted';
    }

    if (Notification.permission === 'denied') {
      return 'denied';
    }

    return Notification.requestPermission();
  };

  const sendMessage = async () => {
    const message = chatInput.trim();
    if (!message) {
      return;
    }

    setIsBusy(true);
    setError(null);

    const optimistic: EventChatMessage = {
      id: `local_${Date.now()}`,
      role: 'customer',
      content: message,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimistic]);
    setChatInput('');

    const result = await customerEventChatService.postChat(eventId, { message });
    if (!result.ok || !result.data?.data?.message) {
      setError(result.error || result.data?.message || 'Failed to send message.');
      setMessages((prev) => prev.filter((item) => item.id !== optimistic.id));
      setIsBusy(false);
      return;
    }

    const [messagesResult, tasksResult] = await Promise.all([
      customerEventChatService.getMessages(eventId),
      customerEventChatService.getTasks(eventId),
    ]);

    if (messagesResult.ok && messagesResult.data?.data?.messages) {
      setMessages(messagesResult.data.data.messages);
    }

    if (tasksResult.ok && tasksResult.data?.data?.tasks) {
      setTasks(tasksResult.data.data.tasks);
    }

    setIsBusy(false);
  };

  const addTask = async () => {
    const title = newTaskTitle.trim();
    if (!title) {
      return;
    }

    setIsBusy(true);
    setError(null);

    const result = await customerEventChatService.createTask(eventId, {
      title,
      needsVendor: false,
      category: 'custom',
    });

    if (!result.ok || !result.data?.data?.task) {
      setError(result.error || result.data?.message || 'Failed to add task.');
      setIsBusy(false);
      return;
    }

    setTasks((prev) => [result.data!.data!.task, ...prev]);
    setNewTaskTitle('');
    setIsBusy(false);
  };

  const updateTaskCompletion = async (taskId: string, completed: boolean) => {
    const result = await customerEventChatService.updateTask(eventId, taskId, { completed });

    if (!result.ok || !result.data?.data?.task) {
      setError(result.error || result.data?.message || 'Failed to update task.');
      return;
    }

    setTasks((prev) => prev.map((task) => (task.id === taskId ? result.data!.data!.task : task)));
  };

  const removeTask = async (taskId: string) => {
    const result = await customerEventChatService.deleteTask(eventId, taskId);
    if (!result.ok) {
      setError(result.error || result.data?.message || 'Failed to delete task.');
      return;
    }

    setTasks((prev) => prev.filter((task) => task.id !== taskId));
  };

  const saveSchedule = async () => {
    setIsBusy(true);
    setError(null);
    setWarning(null);

    const scheduleResult = await customerEventChatService.saveSchedule(eventId, {
      dateTBD,
      startAt: dateTBD ? undefined : `${startDate}T${isAllDay ? '00:00' : startTime}`,
      endAt: !dateTBD && endDate ? `${endDate}T${isAllDay ? '23:59' : endTime}` : undefined,
      timezone,
      isAllDay,
      recurrenceRule: {
        isRecurring,
        frequency: isRecurring ? frequency : undefined,
        endType: isRecurring ? endType : 'never',
        until: isRecurring && endType === 'until' && recurrenceUntil ? recurrenceUntil : undefined,
        count: isRecurring && endType === 'count' ? recurrenceCount : undefined,
      },
    });

    if (!scheduleResult.ok) {
      setError(scheduleResult.error || scheduleResult.data?.message || 'Failed to save schedule.');
      setIsBusy(false);
      return;
    }

    if (scheduleResult.data?.data?.clarification) {
      setWarning(scheduleResult.data.data.clarification);
    }

    setSuccess('Schedule saved.');
    setIsBusy(false);
  };

  const saveReminders = async () => {
    setIsBusy(true);
    setError(null);
    setWarning(null);

    let nextChannels = [...channels];
    let nextPermissionStatus = permissionStatus;

    if (remindersEnabled && channels.includes('push')) {
      const permission = await requestNotificationPermission();
      nextPermissionStatus = permission;
      setPermissionStatus(permission);

      if (permission === 'denied' || permission === 'unsupported') {
        nextChannels = channels.filter((channel) => channel !== 'push');
        setChannels(nextChannels);
        setWarning('Push permission not available. Saved reminders without push channel.');
      }
    }

    const remindersResult = await customerEventChatService.saveReminders(eventId, {
      enabled: remindersEnabled,
      channels: remindersEnabled ? nextChannels : [],
      offsetsMinutes: remindersEnabled ? offsets : [],
      permissionStatus: nextPermissionStatus,
    });

    if (!remindersResult.ok) {
      setError(remindersResult.error || remindersResult.data?.message || 'Failed to save reminders.');
      setIsBusy(false);
      return;
    }

    setSuccess('Reminder settings saved.');
    setIsBusy(false);
  };

  const connectCalendar = async (): Promise<boolean> => {
    setIsBusy(true);
    setError(null);
    setWarning(null);
    setSuccess(null);

    const result = await customerEventChatService.connectCalendar({ provider: selectedProvider });
    if (!result.ok || !result.data?.data?.status) {
      const message = result.error || result.data?.message || 'Failed to connect calendar provider.';
      if (message === GENERIC_ERROR_TEXT) {
        setWarning('Google Calendar service is temporarily unavailable. Continue with local reminders and try again later.');
      } else {
        setError(message);
      }
      setIsBusy(false);
      return false;
    }

    setCalendarStatus(result.data.data.status);
    setSuccess('Calendar connected.');
    setIsBusy(false);
    return true;
  };

  const setCalendarSync = async (enabled: boolean) => {
    setIsBusy(true);
    setError(null);
    setWarning(null);
    setSuccess(null);

    let latestStatus = calendarStatus;
    if (enabled && !latestStatus.connected) {
      const statusResult = await customerEventChatService.getCalendarStatus();
      if (statusResult.ok && statusResult.data?.data?.status) {
        latestStatus = statusResult.data.data.status;
        setCalendarStatus(latestStatus);
      }
    }

    if (enabled && !latestStatus.connected) {
      setWarning('Calendar not connected. Connect provider first or use local reminders only.');
      setIsBusy(false);
      return;
    }

    const result = await customerEventChatService.setCalendarSync(eventId, {
      enabled,
      provider: selectedProvider,
      calendarId: latestStatus.calendarId,
    });

    if (!result.ok) {
      const message = result.error || result.data?.message || 'Failed to update calendar sync.';
      if (message === GENERIC_ERROR_TEXT) {
        setWarning('Calendar sync service is temporarily unavailable. You can still use local reminders.');
      } else {
        setError(message);
      }
      setIsBusy(false);
      return;
    }

    setCalendarSyncEnabled(enabled);
    setSuccess(enabled ? 'Calendar sync enabled.' : 'Calendar sync disabled.');
    setIsBusy(false);
  };

  const summarize = async () => {
    setIsBusy(true);
    setError(null);

    const result = await customerEventChatService.summarize(eventId);
    if (!result.ok || !result.data?.data?.summary) {
      setError(result.error || result.data?.message || 'Failed to summarize event context.');
      setIsBusy(false);
      return;
    }

    setSummary(result.data.data.summary);
    setIsBusy(false);
  };

  const confirmTasks = async () => {
    setIsBusy(true);
    setError(null);

    if (tasks.length === 0) {
      setError('Add at least 1 task before confirming.');
      setIsBusy(false);
      return;
    }

    const result = await customerEventChatService.confirmTasks(eventId);
    if (!result.ok) {
      setError(result.error || result.data?.message || 'Failed to confirm tasks.');
      setIsBusy(false);
      return;
    }

    setEventState(result.data?.data?.eventState || 'active');
    setSuccess('Tasks confirmed and event activated. Redirecting to recommendations...');
    router.push(`/customer/events/${eventId}/recommendations`);
  };

  const toggleOffset = (value: number) => {
    setOffsets((prev) => (prev.includes(value) ? prev.filter((item) => item !== value) : [...prev, value].sort((a, b) => b - a)));
  };

  const toggleChannel = (channel: ReminderChannel) => {
    setChannels((prev) => (prev.includes(channel) ? prev.filter((item) => item !== channel) : [...prev, channel]));
  };

  return {
    isInitialLoading,
    isBusy,
    error,
    warning,
    success,
    eventTitle,
    eventState,
    eventType,
    personaCount,
    messages,
    tasks,
    activeTaskCount,
    chatInput,
    setChatInput,
    sendMessage,
    newTaskTitle,
    setNewTaskTitle,
    addTask,
    updateTaskCompletion,
    removeTask,
    dateTBD,
    setDateTBD,
    startDate,
    setStartDate,
    startTime,
    setStartTime,
    endDate,
    setEndDate,
    endTime,
    setEndTime,
    timezone,
    setTimezone,
    isAllDay,
    setIsAllDay,
    isRecurring,
    setIsRecurring,
    frequency,
    setFrequency,
    endType,
    setEndType,
    recurrenceUntil,
    setRecurrenceUntil,
    recurrenceCount,
    setRecurrenceCount,
    remindersEnabled,
    setRemindersEnabled,
    offsets,
    toggleOffset,
    channels,
    toggleChannel,
    permissionStatus,
    saveSchedule,
    saveReminders,
    calendarProviders,
    selectedProvider,
    setSelectedProvider,
    calendarStatus,
    calendarSyncEnabled,
    connectCalendar,
    setCalendarSync,
    summarize,
    summary,
    confirmTasks,
  };
};
