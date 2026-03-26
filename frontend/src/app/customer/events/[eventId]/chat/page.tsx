'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useEventChatPlanner } from '@/hooks/customer/useEventChatPlanner';
import { ROUTES } from '@/lib/routes';

const toDisplayDate = (isoDate: string): string => {
  if (!isoDate) {
    return '';
  }

  const [year, month, day] = isoDate.split('-');
  if (!year || !month || !day) {
    return '';
  }

  return `${day}/${month}/${year}`;
};

const toIsoDate = (displayDate: string): string | null => {
  const cleaned = displayDate.trim();
  if (!cleaned) {
    return '';
  }

  const matched = cleaned.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!matched) {
    return null;
  }

  const [, dayStr, monthStr, yearStr] = matched;
  const day = Number(dayStr);
  const month = Number(monthStr);
  const year = Number(yearStr);

  const candidate = new Date(year, month - 1, day);
  const isValidDate = candidate.getFullYear() === year && candidate.getMonth() === month - 1 && candidate.getDate() === day;

  if (!isValidDate) {
    return null;
  }

  return `${yearStr}-${monthStr}-${dayStr}`;
};

const todayIso = (): string => {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const isPastIsoDate = (isoDate: string): boolean => {
  const [yearStr, monthStr, dayStr] = isoDate.split('-');
  const year = Number(yearStr);
  const month = Number(monthStr);
  const day = Number(dayStr);

  if (!year || !month || !day) {
    return false;
  }

  const selectedDate = new Date(year, month - 1, day);
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  return selectedDate < today;
};

const normalizeOffsets = (values: number[]): number[] => [...values].sort((a, b) => b - a);
const recurrenceLabelByFrequency: Record<'daily' | 'weekly' | 'monthly' | 'yearly', string> = {
  daily: 'Every Day',
  weekly: 'Every Week',
  monthly: 'Every Month',
  yearly: 'Every Year',
};
type RecurrenceFrequencyOption = 'daily' | 'weekly' | 'monthly' | 'yearly';

export default function CustomerEventChatPage() {
  const params = useParams<{ eventId: string }>();
  const router = useRouter();
  const eventId = params?.eventId;
  const [activeTaskMenuId, setActiveTaskMenuId] = useState<string | null>(null);
  const [showAllTasks, setShowAllTasks] = useState(false);
  const [dateInputValue, setDateInputValue] = useState('');
  const [dateInputError, setDateInputError] = useState<string | null>(null);
  const datePickerRef = useRef<HTMLInputElement>(null);
  const mobileSheetRef = useRef<HTMLDivElement>(null);
  const mobileCloseButtonRef = useRef<HTMLButtonElement>(null);
  const rightPanelRef = useRef<HTMLDivElement>(null);
  const rightPanelCloseButtonRef = useRef<HTMLButtonElement>(null);
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [isMobileViewport, setIsMobileViewport] = useState(false);
  const [isRightPanelOpenMobile, setIsRightPanelOpenMobile] = useState(false);
  const [isRightPanelCollapsedDesktop, setIsRightPanelCollapsedDesktop] = useState(false);
  const [pendingCalendarSyncEnabled, setPendingCalendarSyncEnabled] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [baselineEventId, setBaselineEventId] = useState<string | null>(null);
  const [baselineValues, setBaselineValues] = useState<{
    startDate: string;
    frequency: RecurrenceFrequencyOption;
    offsets: number[];
    calendarSyncEnabled: boolean;
  } | null>(null);

  const {
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
    chatInput,
    setChatInput,
    sendMessage,
    newTaskTitle,
    setNewTaskTitle,
    addTask,
    updateTaskTitle,
    removeTask,
    startDate,
    setStartDate,
    setIsRecurring,
    frequency,
    setFrequency,
    setRemindersEnabled,
    offsets,
    toggleOffset,
    saveSchedule,
    saveReminders,
    calendarStatus,
    calendarSyncEnabled,
    connectCalendar,
    setCalendarSync,
  } = useEventChatPlanner(eventId || '');

  useEffect(() => {
    setDateInputValue(toDisplayDate(startDate));
    setDateInputError(null);
  }, [startDate]);

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const mediaQuery = window.matchMedia('(max-width: 767px)');
    const applyViewportMode = (event?: MediaQueryListEvent) => {
      const nextIsMobile = event ? event.matches : mediaQuery.matches;
      setIsMobileViewport(nextIsMobile);
      if (nextIsMobile) {
        setIsRightPanelOpenMobile(false);
      }
    };

    applyViewportMode();
    mediaQuery.addEventListener('change', applyViewportMode);
    return () => mediaQuery.removeEventListener('change', applyViewportMode);
  }, []);

  useEffect(() => {
    if (isInitialLoading || !eventId) {
      return;
    }

    if (baselineEventId === eventId) {
      return;
    }

    setBaselineValues({
      startDate,
      frequency,
      offsets: normalizeOffsets(offsets),
      calendarSyncEnabled,
    });
    setPendingCalendarSyncEnabled(calendarSyncEnabled);
    setBaselineEventId(eventId);
    setSaveStatus('idle');
    setIsEditorOpen(false);
    setIsRightPanelOpenMobile(false);
  }, [isInitialLoading, eventId, baselineEventId, startDate, frequency, offsets, calendarSyncEnabled]);

  if (!eventId) {
    return <section className="rounded-2xl border border-[#EAEAEA] bg-white p-6 text-sm text-[#EA4335]">Invalid event id.</section>;
  }

  const onSendMessage = (event: FormEvent) => {
    event.preventDefault();
    void sendMessage();
  };

  const onAddTask = async (event: FormEvent) => {
    event.preventDefault();
    if (editingTaskId) {
      const updated = await updateTaskTitle(editingTaskId, newTaskTitle);
      if (updated) {
        setEditingTaskId(null);
        setNewTaskTitle('');
      }
      return;
    }

    await addTask();
  };

  const hasUnsavedChanges = Boolean(
    baselineValues
    && (
      baselineValues.startDate !== startDate
      || baselineValues.frequency !== frequency
      || normalizeOffsets(baselineValues.offsets).join(',') !== normalizeOffsets(offsets).join(',')
      || baselineValues.calendarSyncEnabled !== pendingCalendarSyncEnabled
    ),
  );

  const openRightPanelMobile = () => {
    setIsEditorOpen(false);
    setIsRightPanelOpenMobile(true);
  };

  const closeRightPanelMobile = () => {
    setIsRightPanelOpenMobile(false);
  };

  const onToggleRightPanel = () => {
    if (isMobileViewport) {
      if (isRightPanelOpenMobile) {
        closeRightPanelMobile();
      } else {
        openRightPanelMobile();
      }
      return;
    }

    setIsRightPanelCollapsedDesktop((prev) => !prev);
  };

  const onToggleScheduleEditor = () => {
    setIsEditorOpen((prev) => {
      const next = !prev;
      if (next && isMobileViewport) {
        setIsRightPanelOpenMobile(false);
      }
      return next;
    });
  };

  const waitForStateCommit = async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  };

  const persistAllEventSettingsBeforeNavigate = async (options: {
    blockOnInvalidTypedDate: boolean;
    closeEditorOnSuccess: boolean;
  }): Promise<boolean> => {
    if (isBusy || saveStatus === 'saving') {
      return false;
    }

    const isoDate = toIsoDate(dateInputValue);
    const typedDateInvalid = isoDate === null || (Boolean(isoDate) && isPastIsoDate(isoDate));
    if (typedDateInvalid) {
      if (options.blockOnInvalidTypedDate) {
        if (!dateInputValue.trim()) {
          setDateInputError(null);
        } else if (isoDate === null) {
          setDateInputError('Use format DD/MM/YYYY');
        } else {
          setDateInputError('Please select today or a future date');
        }
        setSaveStatus('error');
        return false;
      }

      // Ignore invalid typed date for draft/confirm flows and keep last valid date.
      setDateInputError(null);
    }

    let effectiveStartDate = startDate;
    if (isoDate && !isPastIsoDate(isoDate) && isoDate !== startDate) {
      setStartDate(isoDate);
      setDateInputValue(toDisplayDate(isoDate));
      effectiveStartDate = isoDate;
      await waitForStateCommit();
    }

    if (!typedDateInvalid) {
      setDateInputError(null);
    }
    setSaveStatus('saving');

    const persisted = await persistScheduleAndReminders();
    if (!persisted) {
      setSaveStatus('error');
      return false;
    }

    if (pendingCalendarSyncEnabled !== calendarSyncEnabled) {
      if (pendingCalendarSyncEnabled && !calendarStatus.connected) {
        const connected = await connectCalendar();
        if (!connected) {
          setSaveStatus('error');
          return false;
        }
      }

      const synced = await setCalendarSync(pendingCalendarSyncEnabled);
      if (!synced) {
        setSaveStatus('error');
        return false;
      }
    }

    setBaselineValues({
      startDate: effectiveStartDate,
      frequency,
      offsets: normalizeOffsets(offsets),
      calendarSyncEnabled: pendingCalendarSyncEnabled,
    });
    setSaveStatus('saved');

    if (options.closeEditorOnSuccess && isMobileViewport) {
      setIsEditorOpen(false);
    }

    return true;
  };

  const onSaveDetails = async (): Promise<boolean> => (
    persistAllEventSettingsBeforeNavigate({
      blockOnInvalidTypedDate: true,
      closeEditorOnSuccess: true,
    })
  );

  const persistScheduleAndReminders = async () => {
    const scheduleSaved = await saveSchedule();
    if (!scheduleSaved) {
      return false;
    }

    const remindersSaved = await saveReminders();
    if (!remindersSaved) {
      return false;
    }

    return true;
  };

  const onSaveDraft = async () => {
    const persisted = await persistAllEventSettingsBeforeNavigate({
      blockOnInvalidTypedDate: false,
      closeEditorOnSuccess: false,
    });
    if (!persisted) {
      return;
    }

    router.replace(ROUTES.CUSTOMER.EVENTS);
  };

  const goToDraftPage = async () => {
    const persisted = await persistAllEventSettingsBeforeNavigate({
      blockOnInvalidTypedDate: false,
      closeEditorOnSuccess: false,
    });
    if (!persisted) {
      return;
    }

    router.push(ROUTES.CUSTOMER.EVENT_DRAFT_REVIEW(eventId || ''));
  };

  const handleCalendarSyncToggle = (nextEnabled: boolean) => {
    setPendingCalendarSyncEnabled(nextEnabled);
  };

  const onCancelScheduleChanges = () => {
    if (!baselineValues) {
      setIsEditorOpen(false);
      return;
    }

    setStartDate(baselineValues.startDate);
    setDateInputValue(toDisplayDate(baselineValues.startDate));
    setDateInputError(null);
    setIsRecurring(true);
    setFrequency(baselineValues.frequency);
    setRemindersEnabled(baselineValues.offsets.length > 0);

    const currentOffsets = normalizeOffsets(offsets);
    const targetOffsets = normalizeOffsets(baselineValues.offsets);
    targetOffsets.forEach((offset) => {
      if (!currentOffsets.includes(offset)) {
        toggleOffset(offset);
      }
    });
    currentOffsets.forEach((offset) => {
      if (!targetOffsets.includes(offset)) {
        toggleOffset(offset);
      }
    });

    setPendingCalendarSyncEnabled(baselineValues.calendarSyncEnabled);
    setSaveStatus('idle');
    setIsEditorOpen(false);
  };

  const commitTypedDate = () => {
    const isoDate = toIsoDate(dateInputValue);

    if (isoDate === null) {
      if (dateInputValue.trim()) {
        setDateInputError('Use format DD/MM/YYYY');
      } else {
        setDateInputError(null);
      }
      return;
    }

    if (isoDate && isPastIsoDate(isoDate)) {
      setDateInputError('Please select today or a future date');
      return;
    }

    setDateInputError(null);
    setStartDate(isoDate);
  };

  useEffect(() => {
    if (saveStatus === 'saved' && hasUnsavedChanges) {
      setSaveStatus('idle');
    }
  }, [saveStatus, hasUnsavedChanges]);

  useEffect(() => {
    if (!(isMobileViewport && isEditorOpen)) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    mobileCloseButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsEditorOpen(false);
        return;
      }

      if (event.key !== 'Tab') {
        return;
      }

      const sheet = mobileSheetRef.current;
      if (!sheet) {
        return;
      }

      const focusable = sheet.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable.length) {
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement as HTMLElement | null;

      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isMobileViewport, isEditorOpen]);

  useEffect(() => {
    if (!(isMobileViewport && isRightPanelOpenMobile)) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    rightPanelCloseButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeRightPanelMobile();
        return;
      }

      if (event.key !== 'Tab') {
        return;
      }

      const panel = rightPanelRef.current;
      if (!panel) {
        return;
      }

      const focusable = panel.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      );
      if (!focusable.length) {
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement as HTMLElement | null;

      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isMobileViewport, isRightPanelOpenMobile]);

  if (isInitialLoading) {
    return <section className="rounded-2xl border border-[#EAEAEA] bg-white p-6 text-sm text-[#666666]">Loading event chat...</section>;
  }

  const visibleMessages = messages.length
    ? messages
    : [
        {
          id: 'empty-assistant',
          role: 'assistant' as const,
          content:
            'Start planning by sharing the date, recurrence, reminders, budget, and must-have details for this event.',
          createdAt: new Date().toISOString(),
        },
      ];
  const sidebarTasks = showAllTasks ? tasks : tasks.slice(0, 3);
  const minSelectableDate = todayIso();
  const recurrenceSummary = recurrenceLabelByFrequency[frequency];
  const reminderSummary = offsets.length
    ? offsets.map((offset) => (offset === 10080 ? '7d' : offset === 1440 ? '1d' : '1h')).join(', ')
    : 'Off';
  const calendarSummary = pendingCalendarSyncEnabled
    ? (calendarStatus.connected ? 'Enabled' : 'Enable on save (connect required)')
    : 'Off';
  const saveStatusText = saveStatus === 'saving'
    ? 'Saving...'
    : saveStatus === 'saved'
      ? 'Saved'
      : saveStatus === 'error'
        ? 'Save failed'
        : hasUnsavedChanges
          ? 'Unsaved changes'
          : 'Up to date';
  const saveStatusClass = saveStatus === 'error'
    ? 'text-[#EA4335]'
    : saveStatus === 'saved'
      ? 'text-[#34A853]'
      : saveStatus === 'saving'
        ? 'text-[#0D47A1]'
        : hasUnsavedChanges
          ? 'text-[#FBBC05]'
          : 'text-[#666666]';

  const openDatePicker = () => {
    const picker = datePickerRef.current;
    if (!picker) {
      return;
    }

    if (typeof picker.showPicker === 'function') {
      picker.showPicker();
      return;
    }

    picker.click();
  };

  const rightPanelContent = (
    <>
      <div className="space-y-8 px-4 py-6 sm:px-6">
        <section>
          <div className="flex items-center justify-between">
            <h3 className="text-[12px] font-semibold uppercase tracking-[0.22em] text-[#666666]">Event Details</h3>
            <span className="rounded-xl bg-[#F4F8FA] px-3 py-1 text-[11px] font-semibold uppercase text-[#666666]">{eventState}</span>
          </div>

          <div className="mt-4 rounded-[20px] border border-[#EAEAEA] bg-white px-5 py-5 shadow-[0_2px_0_rgba(209,217,231,0.55)]">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full border-[4px] border-[#CCCCCC] bg-[#F4F8FA] text-[22px] font-bold text-[#0D47A1]">
                {eventTitle.trim().charAt(0).toUpperCase() || 'E'}
              </div>
              <div className="min-w-0">
                <p className="truncate text-[22px] font-bold leading-none text-[#0D47A1] sm:text-[24px]">{eventTitle || 'Event'}</p>
                <p className="mt-2 text-[14px] leading-none text-[#666666]">{eventType || 'General event'}</p>
              </div>
            </div>

            <div className="mt-5 space-y-2.5 text-[14px] text-[#666666]">
              <p className="flex items-center gap-3 leading-none">
                <img src="/icons/customer/chat/like_icon.svg" alt="likes" className="h-5 w-4" />
                Personas linked: {personaCount}
              </p>
              <p className="flex items-center gap-3 leading-none">
                <img src="/icons/customer/chat/cake.svg" alt="birthday" className="h-5 w-4 shrink-0" />
                Scheduled date: {startDate || 'Date TBD'}
              </p>
            </div>
          </div>
        </section>

        <section>
          <h3 className="text-[12px] font-semibold uppercase tracking-[0.22em] text-[#666666]">Suggested Tasks</h3>

          <div className="mt-4 space-y-3">
            {sidebarTasks.length === 0 ? (
              <div className="rounded-[20px] border border-dashed border-[#D7DFEC] bg-white px-5 py-6 text-sm text-[#666666]">
                No tasks yet. Add tasks in chat to continue planning.
              </div>
            ) : sidebarTasks.map((task) => (
              <div key={task.id} className="flex items-center justify-between rounded-[20px] border border-[#EAEAEA] bg-white px-5 py-4">
                <div className="min-w-0">
                  <p className="text-[15px] font-semibold leading-tight text-[#666666]">{task.title}</p>
                  <p className="mt-1 text-[13px] leading-tight text-[#666666]">{task.category || 'Planning task'}</p>
                </div>

                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setActiveTaskMenuId((prev) => (prev === task.id ? null : task.id))}
                    className="inline-flex h-8 w-8 items-center justify-center rounded-md text-[#666666] hover:bg-[#F4F8FA]"
                    aria-label="Task actions"
                  >
                    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
                      <circle cx="12" cy="5" r="1.8" />
                      <circle cx="12" cy="12" r="1.8" />
                      <circle cx="12" cy="19" r="1.8" />
                    </svg>
                  </button>

                  {activeTaskMenuId === task.id && (
                    <div className="absolute right-0 top-9 z-20 w-28 rounded-lg border border-[#CCCCCC] bg-white p-1 shadow-[0_10px_24px_rgba(22,37,74,0.12)]">
                      <button
                        type="button"
                        onClick={() => {
                          setNewTaskTitle(task.title);
                          setEditingTaskId(task.id);
                          setActiveTaskMenuId(null);
                        }}
                        className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium text-[#666666] hover:bg-[#FAFAFA]"
                      >
                        <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M12 20h9" />
                          <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5Z" />
                        </svg>
                        Edit
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          void removeTask(task.id);
                          setActiveTaskMenuId(null);
                        }}
                        className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium text-[#EA4335] hover:bg-[#FAFAFA]"
                      >
                        <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M3 6h18" />
                          <path d="M8 6V4h8v2" />
                          <path d="M19 6l-1 14H6L5 6" />
                        </svg>
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={() => setShowAllTasks((prev) => !prev)}
            className="mt-5 h-14 w-full rounded-[16px] border-2 border-[#CCCCCC] bg-white text-[14px] font-semibold uppercase tracking-[0.12em] text-[#0D47A1]"
          >
            {showAllTasks ? 'Show Less Tasks' : `View All Tasks (${tasks.length})`}
          </button>

          <form onSubmit={onAddTask} className="mt-4 flex gap-2">
            <input
              value={newTaskTitle}
              onChange={(event) => setNewTaskTitle(event.target.value)}
              placeholder="Add custom task"
              className="h-12 flex-1 rounded-[16px] border-2 border-[#EAEAEA] bg-white px-4 text-sm text-[#666666]"
            />
            <button type="submit" className="h-12 rounded-[16px] border-2 border-[#EAEAEA] bg-white px-5 text-xl font-semibold text-[#666666]">
              {editingTaskId ? 'Save' : '+'}
            </button>
          </form>
        </section>
      </div>

      <div className="mt-auto border-t border-[#EAEAEA] bg-[#F4F8FA] px-6 py-6">
        <button
          type="button"
          onClick={() => void onSaveDraft()}
          disabled={isBusy || saveStatus === 'saving'}
          className="mb-3 h-10 w-full rounded-[12px] border border-[#EAEAEA] bg-white text-[12px] font-semibold uppercase tracking-[0.08em] text-[#666666]"
        >
          Save As Draft
        </button>
        <button
          type="button"
          onClick={() => void goToDraftPage()}
          disabled={isBusy || saveStatus === 'saving'}
          className="h-14 w-full rounded-[18px] bg-[#0D47A1] px-6 text-[13px] font-semibold uppercase tracking-[0.08em] text-white disabled:opacity-60"
        >
          Confirm Tasks & View Recommendations
        </button>
      </div>
    </>
  );

  return (
    <section className="overflow-hidden rounded-2xl border border-[#EAEAEA] bg-white">
      {(error || warning || success) && (
        <div className="space-y-2 border-b border-[#EAEAEA] bg-[#F4F8FA] px-6 py-3 text-sm">
          {error && <p className="rounded-md border border-[#EAEAEA] bg-[#FAFAFA] px-3 py-2 text-[#EA4335]">{error}</p>}
          {warning && <p className="rounded-md border border-[#EAEAEA] bg-[#FAFAFA] px-3 py-2 text-[#FBBC05]">{warning}</p>}
          {success && <p className="rounded-md border border-[#EAEAEA] bg-[#FAFAFA] px-3 py-2 text-[#34A853]">{success}</p>}
        </div>
      )}

      <div className="flex min-h-[820px] flex-col lg:min-h-[780px] lg:flex-row">
        <div
          className={`flex min-w-0 flex-1 flex-col border-b border-[#EAEAEA] lg:border-b-0 ${
            !isMobileViewport && !isRightPanelCollapsedDesktop ? 'lg:border-r' : ''
          }`}
        >
          <header className="border-b border-[#EAEAEA] px-4 py-4 sm:px-6">
            <div className="flex flex-wrap items-center justify-between gap-3 sm:flex-nowrap">
              <div className="min-w-0">
                <h1 className="truncate text-[22px] font-bold leading-tight text-[#0D47A1] sm:text-[36px]">{eventTitle || 'Event'}</h1>
                <div className="mt-1 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#666666] sm:text-[11px] sm:tracking-[0.16em]">
                  <span className="inline-block h-2 w-2 rounded-full bg-[#FBBC05]" />
                  Planning Phase
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onToggleRightPanel}
                  className="inline-flex h-8 items-center gap-1 rounded-lg border border-[#EAEAEA] bg-white px-2.5 text-[11px] font-semibold text-[#666666] sm:h-9 sm:px-3 sm:text-xs"
                >
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 4h18v16H3z" />
                    <path d="M14 4v16" />
                  </svg>
                  {isMobileViewport
                    ? (isRightPanelOpenMobile ? 'Close Panel' : 'Open Panel')
                    : (isRightPanelCollapsedDesktop ? 'Show Panel' : 'Hide Panel')}
                </button>

                <button className="inline-flex h-8 items-center gap-1 rounded-lg border border-[#EAEAEA] bg-white px-2.5 text-[11px] font-semibold text-[#666666] sm:h-9 sm:px-3 sm:text-xs">
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M4 7h16" />
                    <path d="M4 12h10" />
                    <path d="M4 17h8" />
                  </svg>
                  Log
                </button>
              </div>
            </div>
          </header>

          <div className="sticky top-0 z-20 border-b border-[#EAEAEA] bg-[#F4F8FA] px-4 py-3 sm:px-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0 space-y-1">
                <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#666666]">Schedule & Calendar</p>
                <div className="flex flex-wrap gap-2 text-xs text-[#666666]">
                  <span className="rounded-md border border-[#EAEAEA] bg-white px-2 py-1">Date: {dateInputValue || 'Date TBD'}</span>
                  <span className="rounded-md border border-[#EAEAEA] bg-white px-2 py-1">Recurrence: {recurrenceSummary}</span>
                  <span className="rounded-md border border-[#EAEAEA] bg-white px-2 py-1">Reminders: {reminderSummary}</span>
                  <span className="rounded-md border border-[#EAEAEA] bg-white px-2 py-1">Sync: {calendarSummary}</span>
                </div>
                <p className={`text-[11px] font-semibold ${saveStatusClass}`}>{saveStatusText}</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onToggleScheduleEditor}
                  className="h-9 rounded-lg border border-[#EAEAEA] bg-white px-3 text-xs font-semibold text-[#666666]"
                >
                  {isEditorOpen ? 'Close' : 'Edit'}
                </button>
                <button
                  type="button"
                  onClick={() => void onSaveDetails()}
                  disabled={isBusy || saveStatus === 'saving' || !hasUnsavedChanges}
                  className="h-9 rounded-lg bg-[#0D47A1] px-3 text-xs font-semibold text-white disabled:opacity-60"
                >
                  Save
                </button>
              </div>
            </div>

            {isEditorOpen && !isMobileViewport && (
              <div className="mt-3 rounded-xl border border-[#EAEAEA] bg-white p-4">
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  <label className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#666666]">
                    Date
                    <div className="relative mt-2">
                      <input
                        type="text"
                        value={dateInputValue}
                        onChange={(event) => {
                          setDateInputValue(event.target.value);
                          if (dateInputError) {
                            setDateInputError(null);
                          }
                        }}
                        onBlur={commitTypedDate}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter') {
                            event.preventDefault();
                            commitTypedDate();
                          }
                        }}
                        placeholder="DD/MM/YYYY"
                        inputMode="numeric"
                        autoComplete="off"
                        className="h-10 w-full rounded-lg border border-[#CCCCCC] bg-white px-3 pr-10 text-sm text-[#666666] placeholder:text-[#666666]"
                      />

                      <input
                        ref={datePickerRef}
                        type="date"
                        value={startDate}
                        min={minSelectableDate}
                        onChange={(event) => {
                          const selectedDate = event.target.value;
                          if (selectedDate && isPastIsoDate(selectedDate)) {
                            setDateInputError('Please select today or a future date');
                            return;
                          }

                          setStartDate(selectedDate);
                          setDateInputValue(toDisplayDate(selectedDate));
                          setDateInputError(null);
                        }}
                        className="pointer-events-none absolute right-2 top-2 h-6 w-6 opacity-0"
                        tabIndex={-1}
                        aria-hidden="true"
                      />

                      <button
                        type="button"
                        onClick={openDatePicker}
                        className="absolute right-2 top-1/2 inline-flex h-6 w-6 -translate-y-1/2 items-center justify-center"
                        aria-label="Open calendar"
                      >
                        <img src="/icons/customer/events/calander_icon.svg" alt="calendar" className="h-5 w-5 object-contain" />
                      </button>
                    </div>

                    {dateInputError && <p className="mt-1 text-[10px] font-medium normal-case tracking-normal text-[#EA4335]">{dateInputError}</p>}
                  </label>

                  <label className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#666666]">
                    Recurrence
                    <select
                      value={frequency}
                      onChange={(event) => {
                        setIsRecurring(true);
                        setFrequency(event.target.value as typeof frequency);
                      }}
                      className="mt-2 h-10 w-full rounded-lg border border-[#CCCCCC] bg-white px-3 text-sm text-[#666666]"
                    >
                      <option value="yearly">Every Year</option>
                      <option value="monthly">Every Month</option>
                      <option value="weekly">Every Week</option>
                      <option value="daily">Every Day</option>
                    </select>
                  </label>
                </div>

                <div className="mt-3 rounded-xl border border-[#EAEAEA] bg-[#F4F8FA] px-3 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-[#666666]">Google Calendar synchronization</p>
                      <p className="text-xs text-[#9AA6BF]">Changes apply when you save schedule details.</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleCalendarSyncToggle(!pendingCalendarSyncEnabled)}
                      className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors duration-200 ${
                        pendingCalendarSyncEnabled ? 'bg-[#4285F4]' : 'bg-[#CCCCCC]'
                      }`}
                      aria-label="Toggle Google Calendar sync"
                      aria-pressed={pendingCalendarSyncEnabled}
                    >
                      <span
                        className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-[0_2px_4px_rgba(17,35,74,0.3)] transition-transform duration-200 ${
                          pendingCalendarSyncEnabled ? 'translate-x-7' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>

                <div className="mt-3 grid grid-cols-3 gap-2">
                  {[10080, 1440, 60].map((offset) => (
                    <button
                      key={offset}
                      type="button"
                      onClick={() => {
                        setRemindersEnabled(true);
                        toggleOffset(offset);
                      }}
                      className={`h-9 rounded-lg border text-xs font-semibold ${
                        offsets.includes(offset)
                          ? 'border-[#0D47A1] bg-[#F4F8FA] text-[#0D47A1]'
                          : 'border-[#EAEAEA] bg-white text-[#666666]'
                      }`}
                    >
                      {offset === 10080 ? '7 days' : offset === 1440 ? '1 day' : '1 hour'}
                    </button>
                  ))}
                </div>

              </div>
            )}
          </div>

          <div className="flex-1 space-y-6 overflow-y-auto px-4 py-5 sm:space-y-8 sm:px-6 sm:py-6">
            {visibleMessages.map((message) => {
              const isAssistant = message.role === 'assistant' || message.role === 'system';

              return (
                <div
                  key={message.id}
                  className={isAssistant ? 'flex min-w-0 gap-3' : 'flex justify-end'}
                >
                  {isAssistant ? (
                    <img src="/icons/logo.svg" alt="assistant" loading="eager" className="mt-1 h-10 w-10 shrink-0 object-contain" />
                  ) : null}

                  <div className={isAssistant ? 'min-w-0 w-full max-w-[650px]' : 'min-w-0 w-full max-w-[650px] text-right'}>
                    <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#666666]">
                      {isAssistant ? 'Occacia Assistant' : 'You'}
                    </p>

                    <div
                      className={
                        isAssistant
                          ? 'rounded-2xl border border-[#EAEAEA] bg-white p-4'
                          : 'ml-auto inline-block max-w-full break-words rounded-2xl bg-[#0D47A1] px-4 py-3 text-left text-sm text-white shadow-[0_8px_20px_rgba(13,79,180,0.25)]'
                      }
                    >
                      <p className={`break-words text-sm ${isAssistant ? 'text-[#666666]' : ''}`}>
                        {message.content}
                      </p>

                      {!isAssistant ? (
                        <span className="mt-1 inline-flex items-center justify-end gap-0.5 text-[10px] text-[#C9C9C9]" aria-label="Sent">
                          <svg viewBox="0 0 12 12" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <path d="M2 6.4L4.3 8.6L10 3" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          <svg viewBox="0 0 12 12" className="-ml-1.5 h-3 w-3" fill="none" stroke="currentColor" strokeWidth="1.8">
                            <path d="M2 6.4L4.3 8.6L10 3" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </span>
                      ) : null}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="border-t border-[#EAEAEA] bg-[#F4F8FA] px-4 py-4">
            <form onSubmit={onSendMessage} className="rounded-2xl border border-[#EAEAEA] bg-white px-3 py-2">
              <div className="flex items-center gap-3">
                <img src="/icons/customer/chat/file_attache_icon.svg" alt="attach" className="h-5 w-3" />
                <input
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  placeholder="Type a message..."
                  className="h-10 flex-1 bg-transparent text-sm text-[#666666] outline-none placeholder:text-[#C9C9C9]"
                />
                <button type="submit" disabled={isBusy} className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-[#0D47A1] text-white disabled:opacity-60">
                  <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 20l18-8L3 4v6l12 2-12 2z" />
                  </svg>
                </button>
              </div>
            </form>

            <div className="mt-3 flex flex-wrap gap-2">
              {['Add Budget', 'Invite Guest', 'Find Venues'].map((chip) => (
                <button
                  key={chip}
                  type="button"
                  className="h-7 rounded-full border border-[#EAEAEA] bg-white px-3 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#666666]"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          {isRightPanelOpenMobile && isMobileViewport && (
            <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-modal="true" aria-label="Event panel">
              <button
                type="button"
                onClick={closeRightPanelMobile}
                className="absolute inset-0 bg-[rgba(10,21,42,0.45)]"
                aria-label="Close event panel backdrop"
              />

              <div
                ref={rightPanelRef}
                className="absolute bottom-0 right-0 top-0 flex w-[88vw] max-w-[380px] flex-col border-l border-[#EAEAEA] bg-[#F4F8FA] shadow-[-14px_0_30px_rgba(17,35,74,0.18)]"
              >
                <div className="flex items-center justify-between border-b border-[#EAEAEA] bg-white px-4 py-3">
                  <p className="text-sm font-semibold text-[#0D47A1]">Event Panel</p>
                  <button
                    ref={rightPanelCloseButtonRef}
                    type="button"
                    onClick={closeRightPanelMobile}
                    className="h-8 rounded-md border border-[#EAEAEA] px-2 text-xs font-semibold text-[#666666]"
                  >
                    Close
                  </button>
                </div>
                <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
                  {rightPanelContent}
                </div>
              </div>
            </div>
          )}

          {isEditorOpen && isMobileViewport && (
            <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true" aria-label="Edit schedule">
              <button
                type="button"
                onClick={() => setIsEditorOpen(false)}
                className="absolute inset-0 bg-[rgba(10,21,42,0.45)]"
                aria-label="Close schedule editor backdrop"
              />

              <div
                ref={mobileSheetRef}
                className="absolute bottom-0 left-0 right-0 max-h-[88dvh] overflow-hidden rounded-t-2xl border border-[#EAEAEA] bg-white shadow-[0_-14px_30px_rgba(17,35,74,0.18)]"
              >
                <div className="flex items-center justify-between border-b border-[#EAEAEA] px-4 py-3">
                  <p className="text-sm font-semibold text-[#0D47A1]">Edit Schedule</p>
                  <button
                    ref={mobileCloseButtonRef}
                    type="button"
                    onClick={() => setIsEditorOpen(false)}
                    className="h-8 rounded-md border border-[#EAEAEA] px-2 text-xs font-semibold text-[#666666]"
                  >
                    Close
                  </button>
                </div>

                <div className="max-h-[calc(88dvh-140px)] space-y-3 overflow-y-auto px-4 py-4">
                  <label className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#666666]">
                    Date
                    <div className="relative mt-2">
                      <input
                        type="text"
                        value={dateInputValue}
                        onChange={(event) => {
                          setDateInputValue(event.target.value);
                          if (dateInputError) {
                            setDateInputError(null);
                          }
                        }}
                        onBlur={commitTypedDate}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter') {
                            event.preventDefault();
                            commitTypedDate();
                          }
                        }}
                        placeholder="DD/MM/YYYY"
                        inputMode="numeric"
                        autoComplete="off"
                        className="h-10 w-full rounded-lg border border-[#CCCCCC] bg-white px-3 pr-10 text-sm text-[#666666] placeholder:text-[#666666]"
                      />

                      <input
                        ref={datePickerRef}
                        type="date"
                        value={startDate}
                        min={minSelectableDate}
                        onChange={(event) => {
                          const selectedDate = event.target.value;
                          if (selectedDate && isPastIsoDate(selectedDate)) {
                            setDateInputError('Please select today or a future date');
                            return;
                          }

                          setStartDate(selectedDate);
                          setDateInputValue(toDisplayDate(selectedDate));
                          setDateInputError(null);
                        }}
                        className="pointer-events-none absolute right-2 top-2 h-6 w-6 opacity-0"
                        tabIndex={-1}
                        aria-hidden="true"
                      />

                      <button
                        type="button"
                        onClick={openDatePicker}
                        className="absolute right-2 top-1/2 inline-flex h-6 w-6 -translate-y-1/2 items-center justify-center"
                        aria-label="Open calendar"
                      >
                        <img src="/icons/customer/events/calander_icon.svg" alt="calendar" className="h-5 w-5 object-contain" />
                      </button>
                    </div>

                    {dateInputError && <p className="mt-1 text-[10px] font-medium normal-case tracking-normal text-[#EA4335]">{dateInputError}</p>}
                  </label>

                  <label className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#666666]">
                    Recurrence
                    <select
                      value={frequency}
                      onChange={(event) => {
                        setIsRecurring(true);
                        setFrequency(event.target.value as typeof frequency);
                      }}
                      className="mt-2 h-10 w-full rounded-lg border border-[#CCCCCC] bg-white px-3 text-sm text-[#666666]"
                    >
                      <option value="yearly">Every Year</option>
                      <option value="monthly">Every Month</option>
                      <option value="weekly">Every Week</option>
                      <option value="daily">Every Day</option>
                    </select>
                  </label>

                  <div className="rounded-xl border border-[#EAEAEA] bg-[#F4F8FA] px-3 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-[#666666]">Google Calendar synchronization</p>
                        <p className="text-xs text-[#9AA6BF]">Changes apply when you save schedule details.</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleCalendarSyncToggle(!pendingCalendarSyncEnabled)}
                        className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors duration-200 ${
                          pendingCalendarSyncEnabled ? 'bg-[#4285F4]' : 'bg-[#CCCCCC]'
                        }`}
                        aria-label="Toggle Google Calendar sync"
                        aria-pressed={pendingCalendarSyncEnabled}
                      >
                        <span
                          className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-[0_2px_4px_rgba(17,35,74,0.3)] transition-transform duration-200 ${
                            pendingCalendarSyncEnabled ? 'translate-x-7' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    {[10080, 1440, 60].map((offset) => (
                      <button
                        key={offset}
                        type="button"
                        onClick={() => {
                          setRemindersEnabled(true);
                          toggleOffset(offset);
                        }}
                        className={`h-9 rounded-lg border text-xs font-semibold ${
                          offsets.includes(offset)
                            ? 'border-[#0D47A1] bg-[#F4F8FA] text-[#0D47A1]'
                            : 'border-[#EAEAEA] bg-white text-[#666666]'
                        }`}
                      >
                        {offset === 10080 ? '7 days' : offset === 1440 ? '1 day' : '1 hour'}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 border-t border-[#EAEAEA] bg-white px-4 py-3 pb-[calc(env(safe-area-inset-bottom)+0.75rem)]">
                  <button
                    type="button"
                    onClick={onCancelScheduleChanges}
                    className="h-10 rounded-lg border border-[#EAEAEA] bg-white px-3 text-xs font-semibold text-[#666666]"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => void onSaveDetails()}
                    disabled={isBusy || saveStatus === 'saving'}
                    className="h-10 rounded-lg bg-[#0D47A1] px-4 text-xs font-semibold text-white disabled:opacity-60"
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {!isMobileViewport && !isRightPanelCollapsedDesktop && (
          <aside className="flex w-full shrink-0 flex-col border-t border-[#EAEAEA] bg-[#F4F8FA] lg:w-[370px] lg:border-l lg:border-t-0">
            {rightPanelContent}
          </aside>
        )}
      </div>
    </section>
  );
}
