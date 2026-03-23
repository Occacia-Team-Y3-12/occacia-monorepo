'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ArrowRight,
  CalendarDays,
  Clock3,
  FileText,
  LayoutTemplate,
  Plus,
  Sparkles,
} from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { getFallbackEventTypes, normalizeEventTypes } from '@/lib/customerEventTypeOptions';
import { customerEventService } from '@/services/customer/eventServices';
import type { CustomerEventSummary, EventTypeOption } from '@/types/customer';

const formatDate = (value?: string | null) => {
  if (!value) {
    return 'Date TBD';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'Date TBD';
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: '2-digit',
    year: 'numeric',
  }).format(date);
};

const formatStatus = (value: string) => {
  const normalized = value.trim().toLowerCase();
  if (normalized === 'draft') return 'Draft';
  if (normalized === 'active') return 'Active';
  return value || 'Unknown';
};

const statusClasses = (value: string) => {
  const normalized = value.trim().toLowerCase();
  if (normalized === 'draft') {
    return 'border-[#FBBC05]/30 bg-[#FFF8E6] text-[#9D7200]';
  }
  if (normalized === 'active') {
    return 'border-[#34A853]/30 bg-[#F0FBF4] text-[#1F7D46]';
  }
  return 'border-[#D7DFEC] bg-[#F3F6FB] text-[#4A5976]';
};

const getEventHref = (event: CustomerEventSummary) =>
  event.status.trim().toLowerCase() === 'draft'
    ? ROUTES.CUSTOMER.EVENT_CHAT(event.eventId)
    : `/customer/events/${event.eventId}`;

export default function CustomerDashboard() {
  const router = useRouter();
  const [events, setEvents] = useState<CustomerEventSummary[]>([]);
  const [eventTemplates, setEventTemplates] = useState<EventTypeOption[]>(getFallbackEventTypes());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const loadDashboard = async () => {
      setIsLoading(true);
      setError(null);

      const [eventsResult, eventTypesResult] = await Promise.all([
        customerEventService.listEvents({ limit: 100 }),
        customerEventService.getEventTypes(),
      ]);

      if (!active) {
        return;
      }

      if (eventTypesResult.ok && eventTypesResult.data?.data?.eventTypes?.length) {
        setEventTemplates(normalizeEventTypes(eventTypesResult.data.data.eventTypes));
      } else {
        setEventTemplates(getFallbackEventTypes());
      }

      if (!eventsResult.ok) {
        setEvents([]);
        setError(eventsResult.error || 'Failed to load dashboard data.');
        setIsLoading(false);
        return;
      }

      setEvents(eventsResult.data?.items ?? []);
      setIsLoading(false);
    };

    void loadDashboard();

    return () => {
      active = false;
    };
  }, []);

  const dashboardData = useMemo(() => {
    const drafts = events.filter(
      (event) => event.status.trim().toLowerCase() === 'draft'
    );
    const activeEvents = events.filter(
      (event) => event.status.trim().toLowerCase() === 'active'
    );
    const upcoming = [...activeEvents]
      .filter((event) => {
        if (!event.startAt) {
          return false;
        }
        const time = new Date(event.startAt).getTime();
        return !Number.isNaN(time) && time >= Date.now();
      })
      .sort((left, right) => {
        const leftTime = new Date(left.startAt || '').getTime();
        const rightTime = new Date(right.startAt || '').getTime();
        return leftTime - rightTime;
      });

    return {
      total: events.length,
      drafts,
      activeEvents,
      upcoming,
      recent: [...events].sort((left, right) =>
        right.updatedAt.localeCompare(left.updatedAt)
      ),
    };
  }, [events]);

  return (
    <div className="space-y-6 sm:space-y-8">
      <section className="relative overflow-hidden rounded-[28px] border border-[#DCE4F2] bg-[linear-gradient(135deg,#0D47A1_0%,#1562CC_48%,#4285F4_100%)] px-6 py-7 text-white shadow-[0_24px_70px_-34px_rgba(13,71,161,0.34)] sm:px-8 sm:py-9">
        <div className="absolute right-0 top-0 h-full w-[38%] bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.22),transparent_55%)]" />
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/75">
              Customer Dashboard
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">
              Plan and manage your events
            </h1>
            <p className="mt-3 text-sm leading-7 text-white/86 sm:text-base">
              Review drafts, track active events, and continue planning for the
              moments that matter most.
            </p>
          </div>

          <button
            type="button"
            onClick={() => router.push(ROUTES.CUSTOMER.EVENTS_NEW)}
            className="inline-flex items-center justify-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-semibold text-[#0D47A1] transition hover:bg-[#F4F8FA]"
          >
            <Plus className="h-4 w-4" />
            Create Event
          </button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-[22px] border border-[#DCE4F2] bg-white p-5 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-[#5B6780]">Total Events</p>
            <CalendarDays className="h-5 w-5 text-[#4285F4]" />
          </div>
          <p className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-[#0D47A1]">
            {isLoading ? '...' : dashboardData.total}
          </p>
          <p className="mt-2 text-sm text-[#7A87A3]">
            All events currently returned by the customer events API.
          </p>
        </article>

        <article className="rounded-[22px] border border-[#DCE4F2] bg-white p-5 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-[#5B6780]">Draft Events</p>
            <FileText className="h-5 w-5 text-[#FBBC05]" />
          </div>
          <p className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-[#0D47A1]">
            {isLoading ? '...' : dashboardData.drafts.length}
          </p>
          <p className="mt-2 text-sm text-[#7A87A3]">
            Events still in planning flow and not yet activated.
          </p>
        </article>

        <article className="rounded-[22px] border border-[#DCE4F2] bg-white p-5 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-[#5B6780]">Upcoming Active</p>
            <Clock3 className="h-5 w-5 text-[#34A853]" />
          </div>
          <p className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-[#0D47A1]">
            {isLoading ? '...' : dashboardData.upcoming.length}
          </p>
          <p className="mt-2 text-sm text-[#7A87A3]">
            Active events with a future start date.
          </p>
        </article>
      </section>

      <section className="rounded-[24px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#4285F4]">
              Templates
            </p>
            <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[#0D47A1]">
              Start with an event template
            </h2>
            <p className="mt-2 text-sm text-[#5B6780]">
              Choose a starting point and continue in the event creation flow.
            </p>
          </div>
          <LayoutTemplate className="h-6 w-6 text-[#4285F4]" />
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {eventTemplates.map((template) => (
            <button
              key={template.id}
              type="button"
              onClick={() =>
                router.push(
                  `${ROUTES.CUSTOMER.EVENTS_NEW}?template=${encodeURIComponent(template.id)}`
                )
              }
              className="rounded-[20px] border border-[#DCE4F2] bg-[linear-gradient(180deg,#FFFFFF_0%,#F8FBFF_100%)] p-5 text-left transition hover:border-[#BFD0EE] hover:shadow-[0_16px_34px_-24px_rgba(13,71,161,0.28)]"
            >
              <div className="inline-flex rounded-full bg-[#EAF2FF] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#0D47A1]">
                {template.label}
              </div>
              <h3 className="mt-4 text-lg font-semibold text-[#0D47A1]">
                {template.example}
              </h3>
              <p className="mt-2 text-sm leading-6 text-[#5B6780]">
                {template.titlePlaceholder.replace(/^e\.g\.,\s*/i, '')}
              </p>
              <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#0D47A1]">
                Use Template
                <ArrowRight className="h-4 w-4" />
              </span>
            </button>
          ))}
        </div>
      </section>

      {error ? (
        <section className="rounded-[24px] border border-[#F4CDCD] bg-white p-6">
          <p className="text-sm font-medium text-[#B23C3C]">{error}</p>
        </section>
      ) : null}

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,0.75fr)]">
        <article className="rounded-[24px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#4285F4]">
                Recent Events
              </p>
              <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[#0D47A1]">
                Continue where you left off
              </h2>
            </div>
            <Link
              href={ROUTES.CUSTOMER.EVENTS}
              className="inline-flex items-center gap-2 text-sm font-semibold text-[#0D47A1]"
            >
              View All
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          {isLoading ? (
            <p className="mt-6 text-sm text-[#5B6780]">Loading events...</p>
          ) : dashboardData.recent.length === 0 ? (
            <div className="mt-6 rounded-[20px] border border-dashed border-[#D7DFEC] bg-[#FAFBFE] px-5 py-8 text-center">
              <Sparkles className="mx-auto h-8 w-8 text-[#4285F4]" />
              <h3 className="mt-4 text-xl font-semibold text-[#0D47A1]">
                No events yet
              </h3>
              <p className="mx-auto mt-2 max-w-lg text-sm leading-7 text-[#5B6780]">
                Create your first event to start using the real planning flow.
              </p>
              <button
                type="button"
                onClick={() => router.push(ROUTES.CUSTOMER.EVENTS_NEW)}
                className="mt-5 rounded-full bg-[#0D47A1] px-5 py-3 text-sm font-semibold text-white"
              >
                Start Planning
              </button>
            </div>
          ) : (
            <div className="mt-6 space-y-4">
              {dashboardData.recent.slice(0, 5).map((event) => (
                <Link
                  key={event.eventId}
                  href={getEventHref(event)}
                  className="flex flex-col gap-4 rounded-[20px] border border-[#EAEAEA] bg-white px-5 py-4 transition hover:border-[#BFD0EE] hover:bg-[#FAFBFE] sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`inline-flex rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] ${statusClasses(event.status)}`}>
                        {formatStatus(event.status)}
                      </span>
                      <span className="rounded-full bg-[#F3F6FB] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4A5976]">
                        {event.eventType}
                      </span>
                    </div>
                    <h3 className="mt-3 truncate text-lg font-semibold text-[#0D47A1]">
                      {event.title}
                    </h3>
                    <p className="mt-1 text-sm text-[#5B6780]">
                      {formatDate(event.startAt)} • {event.personaIds.length} linked persona{event.personaIds.length === 1 ? '' : 's'}
                    </p>
                  </div>

                  <span className="inline-flex items-center gap-2 text-sm font-semibold text-[#0D47A1]">
                    Open
                    <ArrowRight className="h-4 w-4" />
                  </span>
                </Link>
              ))}
            </div>
          )}
        </article>

        <article className="rounded-[24px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[#4285F4]">
            Planning Queue
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[#0D47A1]">
            Drafts waiting for action
          </h2>

          {isLoading ? (
            <p className="mt-6 text-sm text-[#5B6780]">Loading drafts...</p>
          ) : dashboardData.drafts.length === 0 ? (
            <div className="mt-6 rounded-[20px] border border-dashed border-[#D7DFEC] bg-[#FAFBFE] px-5 py-8 text-center text-sm text-[#5B6780]">
              No draft events are currently waiting for completion.
            </div>
          ) : (
            <div className="mt-6 space-y-3">
              {dashboardData.drafts.slice(0, 4).map((event) => (
                <Link
                  key={event.eventId}
                  href={ROUTES.CUSTOMER.EVENT_CHAT(event.eventId)}
                  className="block rounded-[18px] border border-[#EAEAEA] bg-white px-4 py-4 transition hover:border-[#BFD0EE] hover:bg-[#FAFBFE]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-base font-semibold text-[#0D47A1]">
                        {event.title}
                      </p>
                      <p className="mt-1 text-sm text-[#5B6780]">
                        Continue planning draft event
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 shrink-0 text-[#0D47A1]" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </article>
      </section>
    </div>
  );
}
