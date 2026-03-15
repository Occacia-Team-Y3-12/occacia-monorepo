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

export default function CustomerEventChatPage() {
  const params = useParams<{ eventId: string }>();
  const router = useRouter();
  const eventId = params?.eventId;
  const [activeTaskMenuId, setActiveTaskMenuId] = useState<string | null>(null);
  const [dateInputValue, setDateInputValue] = useState('');
  const [dateInputError, setDateInputError] = useState<string | null>(null);
  const datePickerRef = useRef<HTMLInputElement>(null);

  const {
    isInitialLoading,
    isBusy,
    error,
    warning,
    success,
    eventTitle,
    eventState,
    messages,
    tasks,
    chatInput,
    setChatInput,
    sendMessage,
    newTaskTitle,
    setNewTaskTitle,
    addTask,
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
    confirmTasks,
  } = useEventChatPlanner(eventId || '');

  useEffect(() => {
    setDateInputValue(toDisplayDate(startDate));
    setDateInputError(null);
  }, [startDate]);

  if (!eventId) {
    return <section className="rounded-2xl border border-[#E4E8F2] bg-white p-6 text-sm text-[#D64545]">Invalid event id.</section>;
  }

  const onSendMessage = (event: FormEvent) => {
    event.preventDefault();
    void sendMessage();
  };

  const onAddTask = (event: FormEvent) => {
    event.preventDefault();
    void addTask();
  };

  const onSaveDetails = async () => {
    await saveSchedule();
    await saveReminders();

    if (calendarSyncEnabled && !calendarStatus.connected) {
      const connected = await connectCalendar();
      if (!connected) {
        return;
      }
    }

    if (calendarSyncEnabled) {
      await setCalendarSync(true);
    }
  };

  const handleCalendarSyncToggle = async (nextEnabled: boolean) => {
    if (nextEnabled) {
      if (!calendarStatus.connected) {
        const connected = await connectCalendar();
        if (!connected) {
          return;
        }
      }

      await setCalendarSync(true);
      return;
    }

    await setCalendarSync(false);
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

    setDateInputError(null);
    setStartDate(isoDate);
  };

  if (isInitialLoading) {
    return <section className="rounded-2xl border border-[#E4E8F2] bg-white p-6 text-sm text-[#4F5871]">Loading event chat...</section>;
  }

  const primaryAssistantMessage = messages[0]?.content
    || `I've created a package for ${eventTitle || 'this event'}! Let's refine the schedule. When is the event, and should it repeat yearly?`;

  const visibleTasks = tasks.slice(0, 3);
  const sidebarTasks = [
    {
      key: visibleTasks[0]?.id || 'task-1',
      title: visibleTasks[0]?.title || 'Book High Tea venue',
      subtitle: 'Suggested: The Ritz or Savoy',
    },
    {
      key: visibleTasks[1]?.id || 'task-2',
      title: visibleTasks[1]?.title || 'Order custom flowers',
      subtitle: 'Sarah prefers Pastel Peonies',
    },
    {
      key: visibleTasks[2]?.id || 'task-3',
      title: visibleTasks[2]?.title || 'Buy birthday gift',
      subtitle: 'Check Amazon Wishlist',
    },
  ];

  return (
    <section className="overflow-hidden rounded-2xl border border-[#D9DFEA] bg-white">
      {(error || warning || success) && (
        <div className="space-y-2 border-b border-[#E6EBF3] bg-[#F8FAFE] px-6 py-3 text-sm">
          {error && <p className="rounded-md border border-[#F4CDCD] bg-[#FFF3F3] px-3 py-2 text-[#B23C3C]">{error}</p>}
          {warning && <p className="rounded-md border border-[#F3E2B8] bg-[#FFF8E9] px-3 py-2 text-[#9D7200]">{warning}</p>}
          {success && <p className="rounded-md border border-[#C7E7D0] bg-[#F0FBF4] px-3 py-2 text-[#1F7D46]">{success}</p>}
        </div>
      )}

      <div className="flex min-h-[820px] flex-col lg:min-h-[780px] lg:flex-row">
        <div className="flex min-w-0 flex-1 flex-col border-r border-[#E6EBF3]">
          <header className="border-b border-[#E6EBF3] px-6 py-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h1 className="text-[36px] font-bold leading-tight text-[#131C2E]">{eventTitle || 'Sarah’s Birthday'}</h1>
                <div className="mt-1 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-[#95A0B6]">
                  <span className="inline-block h-2 w-2 rounded-full bg-[#E5A30E]" />
                  Planning Phase
                </div>
              </div>

              <button className="inline-flex h-9 items-center gap-1 rounded-lg border border-[#E0E5EF] bg-white px-3 text-xs font-semibold text-[#36435E]">
                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M4 7h16" />
                  <path d="M4 12h10" />
                  <path d="M4 17h8" />
                </svg>
                Log
              </button>
            </div>
          </header>

          <div className="flex-1 space-y-8 overflow-y-auto px-6 py-6">
            <div className="flex gap-3">
              <img src="/icons/logo.svg" alt="assistant" className="mt-1 h-10 w-10 shrink-0 object-contain" />
              <div className="w-full max-w-[650px]">
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#9AA5BC]">Occacia Assistant</p>
                <div className="rounded-2xl border border-[#E2E7F1] bg-white px-4 py-3 text-sm text-[#46536D]">
                  {primaryAssistantMessage}
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <div className="w-full max-w-[650px] text-right">
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#9AA5BC]">Me</p>
                <div className="ml-auto inline-block rounded-2xl bg-[#0D4FB4] px-4 py-3 text-sm text-white shadow-[0_8px_20px_rgba(13,79,180,0.25)]">
                  <p>It&apos;s on {startDate || '2025-10-11'}. Yes, repeat it every year.</p>
                  <span className="mt-1 inline-flex items-center justify-end gap-0.5 text-[10px] text-[#D6E4FF]" aria-label="Sent">
                    <svg viewBox="0 0 12 12" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path d="M2 6.4L4.3 8.6L10 3" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    <svg viewBox="0 0 12 12" className="-ml-1.5 h-3 w-3" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path d="M2 6.4L4.3 8.6L10 3" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </span>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <img src="/icons/logo.svg" alt="assistant" className="mt-1 h-10 w-10 shrink-0 object-contain" />
              <div className="w-full max-w-[650px]">
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#9AA5BC]">Occacia Assistant</p>
                <div className="rounded-2xl border border-[#DDE4F0] bg-white p-4">
                  <p className="text-sm text-[#4D5971]">
                    Got it! {startDate || 'Oct 11th'}, recurring yearly. Would you like to set reminders for 7 days and 1 day before? Also, would you like to sync this to your Google Calendar?
                  </p>

                  <div className="mt-4 rounded-xl border border-[#DEE5F1] bg-[#F8FAFE] p-4">
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                      <label className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#98A4BC]">
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
                            className="h-10 w-full rounded-lg border border-[#D7DFEC] bg-white px-3 pr-10 text-sm text-[#1C2940] placeholder:text-[#98A4BC]"
                          />

                          <input
                            ref={datePickerRef}
                            type="date"
                            value={startDate}
                            onChange={(event) => {
                              setStartDate(event.target.value);
                              setDateInputError(null);
                            }}
                            className="pointer-events-none absolute right-2 top-2 h-6 w-6 opacity-0"
                            tabIndex={-1}
                            aria-hidden="true"
                          />

                          <button
                            type="button"
                            onClick={() => {
                              const picker = datePickerRef.current;
                              if (!picker) {
                                return;
                              }

                              if (typeof picker.showPicker === 'function') {
                                picker.showPicker();
                                return;
                              }

                              picker.click();
                            }}
                            className="absolute right-2 top-1/2 inline-flex h-6 w-6 -translate-y-1/2 items-center justify-center"
                            aria-label="Open calendar"
                          >
                            <img src="/icons/customer/events/calander_icon.svg" alt="calendar" className="h-5 w-5 object-contain" />
                          </button>
                        </div>

                        {dateInputError && <p className="mt-1 text-[10px] font-medium normal-case tracking-normal text-[#C23D3D]">{dateInputError}</p>}
                      </label>

                      <label className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[#98A4BC]">
                        Recurrence
                        <select
                          value={frequency}
                          onChange={(event) => {
                            setIsRecurring(true);
                            setFrequency(event.target.value as typeof frequency);
                          }}
                          className="mt-2 h-10 w-full rounded-lg border border-[#D7DFEC] bg-white px-3 text-sm text-[#1C2940]"
                        >
                          <option value="yearly">Every Year</option>
                          <option value="monthly">Every Month</option>
                          <option value="weekly">Every Week</option>
                          <option value="daily">Every Day</option>
                        </select>
                      </label>
                    </div>

                    <div className="mt-3 rounded-xl border border-[#DEE5F1] bg-white px-3 py-2">
                      <div className="flex items-center justify-between gap-2">
                        <label className="flex items-center gap-2 text-sm font-semibold text-[#2C3A57]">
                          <input
                            type="checkbox"
                            checked={calendarSyncEnabled}
                            onChange={async (event) => {
                              const enabled = event.target.checked;
                              await handleCalendarSyncToggle(enabled);
                            }}
                          />
                          Sync to Google Calendar
                        </label>
                        <button
                          type="button"
                          onClick={async () => {
                            const nextEnabled = !calendarSyncEnabled;
                            await handleCalendarSyncToggle(nextEnabled);
                          }}
                          className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors duration-200 ${
                            calendarSyncEnabled ? 'bg-[#0F5FD8]' : 'bg-[#C6D2E8]'
                          }`}
                          aria-label="Toggle Google Calendar sync"
                          aria-pressed={calendarSyncEnabled}
                        >
                          <span
                            className={`inline-block h-6 w-6 transform rounded-full bg-white shadow-[0_2px_4px_rgba(17,35,74,0.3)] transition-transform duration-200 ${
                              calendarSyncEnabled ? 'translate-x-7' : 'translate-x-1'
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
                              ? 'border-[#0F4FB7] bg-[#E8F0FF] text-[#0F4FB7]'
                              : 'border-[#D8E0EE] bg-white text-[#5B6883]'
                          }`}
                        >
                          {offset === 10080 ? '7 days' : offset === 1440 ? '1 day' : '1 hour'}
                        </button>
                      ))}
                    </div>

                    <button
                      type="button"
                      onClick={() => void onSaveDetails()}
                      disabled={isBusy}
                      className="mt-4 h-10 w-full rounded-lg bg-[#0F4FB7] text-sm font-semibold text-white disabled:opacity-60"
                    >
                      Confirm & Save Details
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-[#E6EBF3] bg-[#F8FAFE] px-4 py-4">
            <form onSubmit={onSendMessage} className="rounded-2xl border border-[#D9E0EE] bg-white px-3 py-2">
              <div className="flex items-center gap-3">
                <img src="/icons/customer/chat/file_attache_icon.svg" alt="attach" className="h-5 w-3" />
                <input
                  value={chatInput}
                  onChange={(event) => setChatInput(event.target.value)}
                  placeholder="Type a message..."
                  className="h-10 flex-1 bg-transparent text-sm text-[#2A3652] outline-none placeholder:text-[#A1ACC0]"
                />
                <button type="submit" disabled={isBusy} className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-[#0F4FB7] text-white disabled:opacity-60">
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
                  className="h-7 rounded-full border border-[#D8DFED] bg-white px-3 text-[10px] font-semibold uppercase tracking-[0.08em] text-[#657590]"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        </div>

        <aside className="flex w-full shrink-0 flex-col border-t border-[#DEE5F1] bg-[#F4F7FC] lg:w-[370px] lg:border-l lg:border-t-0">
          <div className="space-y-8 px-6 py-6">
            <section>
              <div className="flex items-center justify-between">
                <h3 className="text-[12px] font-semibold uppercase tracking-[0.22em] text-[#8E9BB4]">Event Details</h3>
                <span className="rounded-xl bg-[#E8EEF8] px-3 py-1 text-[11px] font-semibold uppercase text-[#526480]">{eventState}</span>
              </div>

              <div className="mt-4 rounded-[20px] border border-[#D4DEED] bg-white px-5 py-5 shadow-[0_2px_0_rgba(209,217,231,0.55)]">
                <div className="flex items-center gap-4">
                  <img src="/images/customer/events/Sarah.svg" alt="Sarah" className="h-16 w-16 rounded-full border-[4px] border-[#C8D8EF]" />
                  <div className="min-w-0">
                    <p className="whitespace-nowrap text-[24px] font-bold leading-none text-[#192236]">Sarah Rivers</p>
                    <p className="mt-2 text-[14px] leading-none text-[#6D7F9C]">Sister · ISFP Persona</p>
                  </div>
                </div>

                <div className="mt-5 space-y-2.5 text-[14px] text-[#1E2A3F]">
                  <p className="flex items-center gap-3 leading-none">
                    <img src="/icons/customer/chat/like_icon.svg" alt="likes" className="h-5 w-4" />
                    Likes: Nature, Minimalist design
                  </p>
                  <p className="flex items-center gap-3 leading-none">
                    <svg viewBox="0 0 24 24" className="h-5 w-4 text-[#0E4FB5]" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M4 20h16" />
                      <path d="M6 20v-4h12v4" />
                      <path d="M8 16v-3h8v3" />
                      <path d="M10 13v-3h4v3" />
                    </svg>
                    Age: Turning 28
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h3 className="text-[12px] font-semibold uppercase tracking-[0.22em] text-[#8E9BB4]">Suggested Tasks</h3>

              <div className="mt-4 space-y-3">
                {sidebarTasks.map((task) => (
                  <div key={task.key} className="flex items-center justify-between rounded-[20px] border border-[#D4DEED] bg-white px-5 py-4">
                    <div>
                      <p className="text-[15px] font-semibold leading-tight text-[#1A2438]">{task.title}</p>
                      <p className="mt-1 text-[13px] leading-tight text-[#6D7F9C]">{task.subtitle}</p>
                    </div>

                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setActiveTaskMenuId((prev) => (prev === task.key ? null : task.key))}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md text-[#94A3BC] hover:bg-[#EEF3FB]"
                        aria-label="Task actions"
                      >
                        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
                          <circle cx="12" cy="5" r="1.8" />
                          <circle cx="12" cy="12" r="1.8" />
                          <circle cx="12" cy="19" r="1.8" />
                        </svg>
                      </button>

                      {activeTaskMenuId === task.key && (
                        <div className="absolute right-0 top-9 z-20 w-28 rounded-lg border border-[#D7DFEC] bg-white p-1 shadow-[0_10px_24px_rgba(22,37,74,0.12)]">
                          <button
                            type="button"
                            onClick={() => {
                              setNewTaskTitle(task.title);
                              setActiveTaskMenuId(null);
                            }}
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium text-[#30415F] hover:bg-[#F2F6FD]"
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
                              if (!task.key.startsWith('task-')) {
                                void removeTask(task.key);
                              }
                              setActiveTaskMenuId(null);
                            }}
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium text-[#B23C3C] hover:bg-[#FFF3F3]"
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
                className="mt-5 h-14 w-full rounded-[16px] border-2 border-[#BCD0EC] bg-white text-[14px] font-semibold uppercase tracking-[0.12em] text-[#0F4FB7]"
              >
                View All Tasks ({Math.max(tasks.length, 8)})
              </button>

              <form onSubmit={onAddTask} className="mt-4 flex gap-2">
                <input
                  value={newTaskTitle}
                  onChange={(event) => setNewTaskTitle(event.target.value)}
                  placeholder="Add custom task"
                  className="h-12 flex-1 rounded-[16px] border-2 border-[#D4DEED] bg-white px-4 text-sm text-[#2A3652]"
                />
                <button type="submit" className="h-12 rounded-[16px] border-2 border-[#D4DEED] bg-white px-5 text-xl font-semibold text-[#5E708D]">
                  +
                </button>
              </form>
            </section>

            <section>
              <h3 className="text-[12px] font-semibold uppercase tracking-[0.22em] text-[#8E9BB4]">Contextual Files</h3>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="flex h-40 items-center justify-center rounded-[16px] border border-[#C8D4E6] bg-[#DCE5F1]">
                  <svg viewBox="0 0 24 24" className="h-8 w-8 text-[#8F9EB6]" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="5" width="18" height="14" rx="2" />
                    <circle cx="9" cy="10" r="1.3" />
                    <path d="M4 17l5-5 4 4 3-3 4 4" />
                  </svg>
                </div>
                <div className="flex h-40 items-center justify-center rounded-[16px] border border-[#C8D4E6] bg-[#DCE5F1]">
                  <svg viewBox="0 0 24 24" className="h-8 w-8 text-[#8F9EB6]" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                    <path d="M14 3v6h6" />
                    <path d="M8 14h8" />
                    <path d="M8 18h6" />
                  </svg>
                </div>
              </div>
            </section>
          </div>

          <div className="mt-auto border-t border-[#DDE5F2] bg-[#F4F7FC] px-6 py-6">
            <button
              type="button"
              onClick={() => router.push(ROUTES.CUSTOMER.EVENT_DRAFT_REVIEW(eventId || ''))}
              className="mb-3 h-10 w-full rounded-[12px] border border-[#D3DEEF] bg-white text-[12px] font-semibold uppercase tracking-[0.08em] text-[#3C4C6D]"
            >
              Save As Draft
            </button>
            <button
              type="button"
              onClick={() => void confirmTasks()}
              disabled={isBusy}
              className="h-14 w-full rounded-[18px] bg-[#0F4FB7] px-6 text-[13px] font-semibold uppercase tracking-[0.08em] text-white disabled:opacity-60"
            >
              Confirm Tasks & View Recommendations
            </button>
          </div>
        </aside>
      </div>
    </section>
  );
}
