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
    const scheduleSaved = await saveSchedule();
    if (!scheduleSaved) {
      return;
    }

    const remindersSaved = await saveReminders();
    if (!remindersSaved) {
      return;
    }

    router.replace(ROUTES.CUSTOMER.EVENTS);
  };

  const onAddCustomTask = () => {
    router.push(ROUTES.CUSTOMER.EVENT_CHAT(eventId || ''));
  };

  return (
    <section className="relative min-h-[calc(100vh-96px)] bg-[#F3F5F9] pb-[calc(120px+env(safe-area-inset-bottom))] pt-8 sm:pt-10">
      {(error || warning || success) && (
        <div className="mx-auto mb-4 max-w-[1120px] space-y-2 text-sm">
          {error && <p className="rounded-md border border-[#F4CDCD] bg-[#FFF3F3] px-3 py-2 text-[#B23C3C]">{error}</p>}
          {warning && <p className="rounded-md border border-[#F3E2B8] bg-[#FFF8E9] px-3 py-2 text-[#9D7200]">{warning}</p>}
          {success && <p className="rounded-md border border-[#C7E7D0] bg-[#F0FBF4] px-3 py-2 text-[#1F7D46]">{success}</p>}
        </div>
      )}

      <div className="mx-auto max-w-[1060px] px-4 sm:px-6">
        <section className="relative overflow-hidden rounded-[28px] border border-[#DCE4F2] bg-[linear-gradient(135deg,#0D47A1_0%,#1562CC_48%,#4285F4_100%)] px-6 py-7 text-white shadow-[0_24px_70px_-34px_rgba(13,71,161,0.34)] sm:px-8 sm:py-9">
          <div className="absolute right-0 top-0 h-full w-[38%] bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.22),transparent_55%)]" />
          <div className="relative max-w-2xl">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/75">
              Event Review
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">
              Review your event plan
            </h1>
            <p className="mt-3 text-sm leading-7 text-white/86 sm:text-base">
              Confirm the generated task list and details before activating your event.
            </p>
          </div>
        </section>

        <div className="mt-7 overflow-hidden rounded-[22px] border border-[#DCE4F2] bg-white shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
          <div className="p-6 sm:p-7">
            <div className="flex items-start justify-between gap-3">
              <div>
                <span className="inline-flex rounded-full bg-[#EAF1FF] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#3F66AC]">
                  Event Preview
                </span>
                <h2 className="mt-3 text-2xl font-semibold leading-tight text-[#0D47A1] sm:text-3xl">
                  {eventTitle || 'Untitled Event'}
                </h2>
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
                    <p className="text-xs font-semibold uppercase tracking-[0.1em] text-[#7A87A3]">Date</p>
                    <p className="text-sm font-semibold leading-tight text-[#4A5976] sm:text-base">{formatDateLabel(startDate)}</p>
                  </div>
                </div>

                <div className="flex items-start gap-2.5">
                  <Image src="/icons/customer/event_draft/remainder.svg" alt="reminders" width={20} height={21} className="mt-0.5 h-[21px] w-5" />
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.1em] text-[#7A87A3]">Reminders</p>
                    <p className="text-sm font-semibold leading-tight text-[#4A5976] sm:text-base">{reminderText}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <Image src="/icons/customer/event_draft/recurrence.svg" alt="recurrence" width={18} height={18} className="mt-0.5 h-[18px] w-[18px]" />
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.1em] text-[#7A87A3]">Recurrence</p>
                  <p className="text-sm font-semibold leading-tight text-[#4A5976] sm:text-base">{frequencyLabel(frequency)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h3 className="text-2xl font-semibold leading-tight text-[#0D47A1] sm:text-3xl">Generated Task List</h3>
          <button
            type="button"
            onClick={onAddCustomTask}
            className="inline-flex items-center gap-2 rounded-full border border-[#DCE4F2] bg-white px-4 py-2 text-sm font-semibold text-[#0D47A1] shadow-[0_8px_20px_-14px_rgba(13,71,161,0.24)]">
            <svg viewBox="0 0 20 20" className="h-[18px] w-[18px]" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="10" cy="10" r="7" />
              <path d="M10 7v6" />
              <path d="M7 10h6" />
            </svg>
            Add Custom Task
          </button>
        </div>

        {displayTasks.length === 0 ? (
          <div className="mt-5 rounded-[14px] border border-dashed border-[#DCE4F2] bg-white px-5 py-8 text-center text-sm text-[#7A87A3]">
            No tasks have been generated for this event yet. Go back to chat to add planning details and tasks.
          </div>
        ) : (
          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
            {displayTasks.map((task) => (
              <div key={task.id} className="flex min-h-[90px] items-center gap-3 rounded-[18px] border border-[#DCE4F2] bg-white px-4 py-3.5 shadow-[0_12px_36px_-30px_rgba(13,71,161,0.18)]">
                <div className="min-w-0">
                  <span className="block text-base font-semibold leading-tight text-[#0D47A1] sm:text-lg">{task.title}</span>
                  <span className="mt-1 inline-flex items-center gap-1 rounded-[4px] bg-[#F3F6FB] px-2 py-0.5 text-xs font-medium text-[#5B6780]">
                    <Image src="/icons/customer/event_draft/calander_icon.svg" alt="task" width={14} height={15} className="h-[12px] w-[12px]" />
                    {task.category || 'Planning'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

       <footer className="fixed inset-x-0 bottom-0 border-t border-[#D6DEEC] bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1060px] flex-col items-stretch gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 pb-[calc(env(safe-area-inset-bottom)+16px)]">
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

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-6 lg:gap-8">
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
              className="inline-flex h-[52px] items-center justify-center gap-2 rounded-[14px] bg-[#0F4FB7] px-6 text-[14px] font-semibold text-white shadow-[0_6px_14px_rgba(15,79,183,0.28)] sm:px-8 sm:text-[15px] lg:text-[16px] disabled:opacity-60"
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
