'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { CalendarDays, ChevronRight, Clock3, Plus, Search } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { customerEventService } from '@/services/customer/eventServices';
import type { CustomerEventSummary } from '@/types/customer';

type EventStatusFilter = 'all' | 'draft' | 'active';

const statusLabel = (status: string) => {
  const normalized = status.trim().toLowerCase();
  if (normalized === 'draft') {
    return 'Draft';
  }
  if (normalized === 'active') {
    return 'Active';
  }
  return status || 'Unknown';
};

const statusClasses = (status: string) => {
  const normalized = status.trim().toLowerCase();
  if (normalized === 'draft') {
    return 'border-[#FBBC05]/30 bg-[#FFF8E6] text-[#9D7200]';
  }
  if (normalized === 'active') {
    return 'border-[#34A853]/30 bg-[#F0FBF4] text-[#1F7D46]';
  }
  return 'border-[#D7DFEC] bg-[#F3F6FB] text-[#4A5976]';
};

const formatEventDate = (value?: string | null) => {
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

const formatUpdatedAt = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'Updated recently';
  }

  return `Updated ${new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: '2-digit',
  }).format(date)}`;
};

const getEventHref = (event: CustomerEventSummary) =>
  event.status.trim().toLowerCase() === 'draft'
    ? ROUTES.CUSTOMER.EVENT_CHAT(event.eventId)
    : `/customer/events/${event.eventId}`;

export default function EventsPage() {
  const [events, setEvents] = useState<CustomerEventSummary[]>([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<EventStatusFilter>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const loadEvents = async () => {
      setIsLoading(true);
      setError(null);

      const result = await customerEventService.listEvents({ limit: 100 });

      if (!active) {
        return;
      }

      if (!result.ok) {
        setEvents([]);
        setError(result.error || 'Failed to load events.');
        setIsLoading(false);
        return;
      }

      setEvents(result.data?.items ?? []);
      setIsLoading(false);
    };

    void loadEvents();

    return () => {
      active = false;
    };
  }, []);

  const filteredEvents = useMemo(() => {
    const normalizedQuery = search.trim().toLowerCase();

    return events.filter((event) => {
      const matchesStatus =
        statusFilter === 'all' ||
        event.status.trim().toLowerCase() === statusFilter;
      const matchesQuery =
        normalizedQuery.length === 0 ||
        event.title.toLowerCase().includes(normalizedQuery) ||
        String(event.description ?? '').toLowerCase().includes(normalizedQuery) ||
        event.eventType.toLowerCase().includes(normalizedQuery);

      return matchesStatus && matchesQuery;
    });
  }, [events, search, statusFilter]);

  return (
    <div className="min-h-screen bg-[#F7F9FC] px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <section className="overflow-hidden rounded-[28px] border border-[#DCE4F2] bg-white shadow-[0_24px_70px_-34px_rgba(13,71,161,0.16)]">
          <div className="bg-[radial-gradient(circle_at_top_left,rgba(66,133,244,0.16),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(52,168,83,0.12),transparent_28%)] px-6 py-8 sm:px-8">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#4285F4]">
                  Customer Events
                </p>
                <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-[#0D47A1] sm:text-4xl">
                  Manage your real event pipeline
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-7 text-[#5B6780] sm:text-base">
                  Review draft plans, continue planning active events, and jump back
                  into the exact flow each event needs next.
                </p>
              </div>

              <Link
                href={ROUTES.CUSTOMER.EVENTS_NEW}
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[#0D47A1] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#0B3D88]"
              >
                <Plus className="h-4 w-4" />
                Create Event
              </Link>
            </div>
          </div>
        </section>

        <section className="rounded-[24px] border border-[#DCE4F2] bg-white p-5 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)] sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="relative w-full lg:max-w-md">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#7A87A3]" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search by title, type, or description"
                className="h-12 w-full rounded-2xl border border-[#D7DFEC] bg-[#FAFBFE] pl-11 pr-4 text-sm text-[#22314D] outline-none transition focus:border-[#4285F4]"
              />
            </div>

            <div className="flex flex-wrap gap-2">
              {(['all', 'draft', 'active'] as const).map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setStatusFilter(value)}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    statusFilter === value
                      ? 'bg-[#0D47A1] text-white'
                      : 'border border-[#D7DFEC] bg-white text-[#4A5976]'
                  }`}
                >
                  {value === 'all'
                    ? 'All'
                    : value.charAt(0).toUpperCase() + value.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </section>

        {isLoading ? (
          <section className="rounded-[24px] border border-[#DCE4F2] bg-white p-8 text-sm text-[#5B6780]">
            Loading customer events...
          </section>
        ) : error ? (
          <section className="rounded-[24px] border border-[#F4CDCD] bg-white p-8">
            <p className="text-sm font-medium text-[#B23C3C]">{error}</p>
          </section>
        ) : filteredEvents.length === 0 ? (
          <section className="rounded-[24px] border border-[#DCE4F2] bg-white p-10 text-center shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#0D47A1] text-white">
              <CalendarDays className="h-6 w-6" />
            </div>
            <h2 className="mt-5 text-2xl font-semibold tracking-[-0.04em] text-[#0D47A1]">
              {events.length === 0 ? 'No events yet' : 'No events match this filter'}
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-[#5B6780]">
              {events.length === 0
                ? 'Create your first event to start planning with real backend data.'
                : 'Try a broader search or switch the status filter.'}
            </p>
            <div className="mt-7 flex justify-center gap-3">
              {events.length > 0 ? (
                <button
                  type="button"
                  onClick={() => {
                    setSearch('');
                    setStatusFilter('all');
                  }}
                  className="rounded-full border border-[#D7DFEC] bg-white px-5 py-3 text-sm font-semibold text-[#4A5976]"
                >
                  Reset Filters
                </button>
              ) : null}
              <Link
                href={ROUTES.CUSTOMER.EVENTS_NEW}
                className="rounded-full bg-[#0D47A1] px-5 py-3 text-sm font-semibold text-white"
              >
                Create Event
              </Link>
            </div>
          </section>
        ) : (
          <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {filteredEvents.map((event) => (
              <article
                key={event.eventId}
                className="flex h-full flex-col rounded-[24px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2">
                    <span
                      className={`inline-flex rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] ${statusClasses(event.status)}`}
                    >
                      {statusLabel(event.status)}
                    </span>
                    <h2 className="text-xl font-semibold tracking-[-0.03em] text-[#0D47A1]">
                      {event.title}
                    </h2>
                  </div>

                  <span className="rounded-full bg-[#F3F6FB] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-[#4A5976]">
                    {event.eventType}
                  </span>
                </div>

                <p className="mt-4 flex-1 break-words text-sm leading-7 text-[#5B6780] line-clamp-3">
                  {event.description?.trim() || 'No description added yet.'}
                </p>

                <div className="mt-5 space-y-3 text-sm text-[#4A5976]">
                  <div className="flex items-center gap-2">
                    <CalendarDays className="h-4 w-4 text-[#4285F4]" />
                    <span>{formatEventDate(event.startAt)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock3 className="h-4 w-4 text-[#34A853]" />
                    <span>{formatUpdatedAt(event.updatedAt)}</span>
                  </div>
                  <div className="text-xs font-medium uppercase tracking-[0.1em] text-[#7A87A3]">
                    {event.personaIds.length} linked persona{event.personaIds.length === 1 ? '' : 's'}
                  </div>
                </div>

                <Link
                  href={getEventHref(event)}
                  className="mt-6 inline-flex items-center justify-between rounded-2xl bg-[#0D47A1] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#0B3D88]"
                >
                  <span>
                    {event.status.trim().toLowerCase() === 'draft'
                      ? 'Continue Planning'
                      : 'Open Event'}
                  </span>
                  <ChevronRight className="h-4 w-4" />
                </Link>
              </article>
            ))}
          </section>
        )}
      </div>
    </div>
  );
}
