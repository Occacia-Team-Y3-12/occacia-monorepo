'use client';

import { useMemo } from 'react';
import Image from 'next/image';
import { useParams, useRouter } from 'next/navigation';
import { useEventChatPlanner } from '@/hooks/customer/useEventChatPlanner';
import { ROUTES } from '@/lib/routes';

const formatDateLabel = (date: string): string => {
  if (!date) {
    return 'Date TBD';
  }

  const dt = new Date(`${date}T00:00:00`);
  if (Number.isNaN(dt.getTime())) {
    return 'Date TBD';
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: '2-digit',
    year: 'numeric',
  }).format(dt);
};

const frequencyLabel = (frequency: 'daily' | 'weekly' | 'monthly' | 'yearly') => {
  if (frequency === 'daily') {
    return 'Daily Recurrence';
  }
  if (frequency === 'weekly') {
    return 'Weekly Recurrence';
  }
  if (frequency === 'monthly') {
    return 'Monthly Recurrence';
  }

  return 'Yearly Recurrence';
};

const offsetLabel = (offset: number) => {
  if (offset % 1440 === 0) {
    const days = offset / 1440;
    return `${days} day${days > 1 ? 's' : ''}`;
  }

  if (offset >= 60) {
    const hours = offset / 60;
    return `${hours} hour${hours > 1 ? 's' : ''}`;
  }

  return `${offset} min`;
};

export default function CustomerEventDraftPage() {
  const params = useParams<{ eventId: string }>();
  const router = useRouter();
  const eventId = params?.eventId;

  const {
    isInitialLoading,
    isBusy,
    error,
    warning,
    success,
    eventTitle,
    tasks,
    startDate,
    frequency,
    offsets,
    updateTaskCompletion,
    saveSchedule,
    saveReminders,
    confirmTasks,
  } = useEventChatPlanner(eventId || '');

  const reminderText = useMemo(() => {
    if (!offsets.length) {
      return 'No reminders';
    }

    const normalized = [...offsets].sort((a, b) => b - a).slice(0, 2);
    return `${normalized.map(offsetLabel).join(' & ')} before`;
  }, [offsets]);

  const displayTasks = useMemo(() => tasks, [tasks]);

  if (!eventId) {
    return <section className="rounded-2xl border border-[#E4E8F2] bg-white p-6 text-sm text-[#D64545]">Invalid event id.</section>;
  }

  if (isInitialLoading) {
    return <section className="rounded-2xl border border-[#E4E8F2] bg-white p-6 text-sm text-[#4F5871]">Loading draft review...</section>;
  }

  const onSaveDraft = async () => {
    await saveSchedule();
    await saveReminders();
  };

  const onAddCustomTask = () => {
    router.push(ROUTES.CUSTOMER.EVENT_CHAT(eventId || ''));
  };

  return (
    <section className="relative min-h-[calc(100vh-96px)] bg-[#F3F5F9] pb-28 pt-10">
      {(error || warning || success) && (
        <div className="mx-auto mb-4 max-w-[1120px] space-y-2 text-sm">
          {error && <p className="rounded-md border border-[#F4CDCD] bg-[#FFF3F3] px-3 py-2 text-[#B23C3C]">{error}</p>}
          {warning && <p className="rounded-md border border-[#F3E2B8] bg-[#FFF8E9] px-3 py-2 text-[#9D7200]">{warning}</p>}
          {success && <p className="rounded-md border border-[#C7E7D0] bg-[#F0FBF4] px-3 py-2 text-[#1F7D46]">{success}</p>}
        </div>
      )}

      <div className="mx-auto max-w-[1060px]">
        <h1 className="text-[32px] font-bold leading-[1.08] tracking-[-0.01em] text-[#1A2438] sm:text-[38px] lg:text-[44px]">Review Your Event Plan</h1>
        <p className="mt-2 text-[13px] text-[#74839D] sm:text-[14px] lg:text-[18px]">Confirm the generated task list and details for your upcoming celebration.</p>

        <div className="mt-7 overflow-hidden rounded-[16px] border border-[#D5DEEC] bg-white shadow-[0_1px_0_rgba(24,39,75,0.06)]">
          <div className="grid grid-cols-1 md:grid-cols-[330px_minmax(0,1fr)] md:items-stretch">
            <div className="relative min-h-[230px] overflow-hidden bg-[#BFDDF3] md:h-auto md:min-h-full">
              <Image src="/images/customer/event_draft/cake_image.svg" alt="Event visual" fill className="object-cover object-center" />
            </div>

            <div className="p-6 sm:p-7">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="inline-flex rounded-full bg-[#EAF1FF] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#3F66AC]">
                    Event Preview
                  </span>
                  <h2 className="mt-3 text-[24px] font-bold leading-tight text-[#1C263A] sm:text-[28px] lg:text-[32px]">{eventTitle || 'Untitled Event'}</h2>
                </div>

                <button
                  type="button"
                  onClick={() => router.push(ROUTES.CUSTOMER.EVENT_CHAT(eventId || ''))}
                  className="inline-flex h-8 w-8 items-center justify-center text-[#95A0B5]"
                  aria-label="Edit in chat"
                >
                  <Image src="/icons/customer/event_draft/pencil.svg" alt="edit" width={18} height={18} />
                </button>
              </div>

              <div className="mt-6 grid grid-cols-1 gap-y-4 sm:grid-cols-2 sm:gap-x-10">
                <div className="space-y-4">
                  <div className="flex items-start gap-2.5">
                    <Image src="/icons/customer/event_draft/date.svg" alt="date" width={18} height={20} className="mt-0.5 h-5 w-[18px]" />
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#95A2B9]">Date</p>
                      <p className="text-[13px] font-semibold leading-tight text-[#26334C] sm:text-[14px] lg:text-[15px]">{formatDateLabel(startDate)}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5">
                    <Image src="/icons/customer/event_draft/remainder.svg" alt="reminders" width={20} height={21} className="mt-0.5 h-[21px] w-5" />
                    <div>
                      <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#95A2B9]">Reminders</p>
                      <p className="text-[13px] font-semibold leading-tight text-[#26334C] sm:text-[14px] lg:text-[15px]">{reminderText}</p>
                    </div>
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <Image src="/icons/customer/event_draft/recurrence.svg" alt="recurrence" width={18} height={18} className="mt-0.5 h-[18px] w-[18px]" />
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[#95A2B9]">Recurrence</p>
                    <p className="text-[13px] font-semibold leading-tight text-[#26334C] sm:text-[14px] lg:text-[15px]">{frequencyLabel(frequency)}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-10 flex items-center justify-between gap-3">
          <h3 className="text-[28px] font-bold leading-tight text-[#1B263C] sm:text-[30px] lg:text-[34px]">Generated Task List</h3>
          <button
            type="button"
            onClick={onAddCustomTask}
            className="inline-flex items-center gap-1 text-[14px] font-semibold text-[#0F4FB7] sm:text-[15px] lg:text-[16px]"
          >
            <svg viewBox="0 0 20 20" className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="10" cy="10" r="7" />
              <path d="M10 7v6" />
              <path d="M7 10h6" />
            </svg>
            Add Custom Task
          </button>
        </div>

        {displayTasks.length === 0 ? (
          <div className="mt-5 rounded-[14px] border border-dashed border-[#D7DFEC] bg-white px-5 py-8 text-center text-sm text-[#74839D]">
            No tasks have been generated for this event yet. Go back to chat to add planning details and tasks.
          </div>
        ) : (
          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            {displayTasks.map((task) => (
              <label key={task.id} className="flex min-h-[90px] items-center gap-3 rounded-[14px] border border-[#D7DFEC] bg-white px-4 py-3.5">
                <input
                  type="checkbox"
                  checked={task.completed}
                  onChange={(event) => {
                    void updateTaskCompletion(task.id, event.target.checked);
                  }}
                  className="mt-0.5 h-[18px] w-[18px] rounded-[4px] border border-[#C2CDE1] accent-[#0F4FB7]"
                />

                <span className="min-w-0">
                  <span className="block text-[16px] font-semibold leading-tight text-[#1D273C] sm:text-[17px] lg:text-[18px]">{task.title}</span>
                  <span className="mt-1 inline-flex items-center gap-1 rounded-[4px] bg-[#F3F6FB] px-2 py-0.5 text-[10px] font-medium text-[#7988A3] sm:text-[11px] lg:text-[12px]">
                    <Image src="/icons/customer/event_draft/calander_icon.svg" alt="task" width={14} height={15} className="h-[12px] w-[12px]" />
                    {task.category || 'Planning'}
                  </span>
                </span>
              </label>
            ))}
          </div>
        )}
      </div>

       <footer className="fixed inset-x-0 bottom-0 border-t border-[#D6DEEC] bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1060px] items-center justify-between gap-3 px-0 py-4">
          <button
            type="button"
            onClick={() => router.push(ROUTES.CUSTOMER.EVENT_CHAT(eventId || ''))}
            className="inline-flex h-11 items-center gap-2 rounded-xl px-2 text-[14px] font-medium text-[#4A5976] sm:text-[15px] lg:text-[16px]"
          >
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 18 9 12l6-6" />
            </svg>
            Back to Chat
          </button>

          <div className="flex items-center gap-4 sm:gap-6 lg:gap-8">
            <button
              type="button"
              onClick={() => void onSaveDraft()}
              disabled={isBusy}
              className="h-11 rounded-xl px-2 text-[14px] font-semibold text-[#415377] sm:text-[15px] lg:text-[16px] disabled:opacity-60"
            >
              Save as Draft
            </button>

            <button
              type="button"
              onClick={() => void confirmTasks()}
              disabled={isBusy}
              className="inline-flex h-[52px] items-center gap-2 rounded-[14px] bg-[#0F4FB7] px-8 text-[14px] font-semibold text-white shadow-[0_6px_14px_rgba(15,79,183,0.28)] sm:text-[15px] lg:text-[16px] disabled:opacity-60"
            >
              Confirm & Activate Event
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M5 13 2 22l9-3 11-11-6-6L5 13Z" />
                <path d="m14 4 6 6" />
              </svg>
            </button>
          </div>
        </div>
      </footer>
    </section>
  );
}
