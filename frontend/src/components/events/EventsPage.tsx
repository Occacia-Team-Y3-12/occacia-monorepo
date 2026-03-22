'use client';

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  defaultEventFilters,
  eventCategories,
  eventLocations,
  getFilteredAndSortedEvents,
  mockEvents,
} from '@/data/mockEvents';
import { EventsFilters } from '@/components/events/EventsFilters';
import { EventsGrid } from '@/components/events/EventsGrid';
import { EventsHeader } from '@/components/events/EventsHeader';
import type { EventFiltersState } from '@/types/eventDiscovery';

const INITIAL_VISIBLE_COUNT = 6;
const LOAD_MORE_COUNT = 3;
const LOADING_DELAY_MS = 420;

export default function EventsPage() {
  const [filters, setFilters] = useState<EventFiltersState>(defaultEventFilters);
  const [visibleCount, setVisibleCount] = useState(INITIAL_VISIBLE_COUNT);
  const [isLoading, setIsLoading] = useState(true);

  const filteredEvents = useMemo(
    () => getFilteredAndSortedEvents(mockEvents, filters),
    [filters],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => setIsLoading(false), 650);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    setIsLoading(true);
    setVisibleCount(INITIAL_VISIBLE_COUNT);

    const timer = window.setTimeout(() => setIsLoading(false), LOADING_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [filters]);

  function handleFilterChange<K extends keyof EventFiltersState>(
    key: K,
    value: EventFiltersState[K],
  ) {
    setFilters((currentFilters) => ({
      ...currentFilters,
      [key]: value,
    }));
  }

  function handleReset() {
    setFilters(defaultEventFilters);
  }

  function handleLoadMore() {
    setVisibleCount((currentCount) => currentCount + LOAD_MORE_COUNT);
  }

  return (
    <div className="relative overflow-hidden bg-[#FAFAFA] px-0 py-2 sm:py-4">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[340px] bg-[radial-gradient(circle_at_top_left,rgba(66,133,244,0.18),transparent_36%),radial-gradient(circle_at_top_right,rgba(13,71,161,0.16),transparent_32%),radial-gradient(circle_at_bottom,rgba(52,168,83,0.12),transparent_30%)]" />
      <div className="pointer-events-none absolute left-[-5rem] top-28 -z-10 h-52 w-52 rounded-full bg-[#4285F4]/15 blur-3xl sm:left-[-3rem] sm:h-72 sm:w-72" />
      <div className="pointer-events-none absolute bottom-8 right-[-5rem] -z-10 h-56 w-56 rounded-full bg-[#34A853]/10 blur-3xl sm:h-80 sm:w-80" />

      <div className="mx-auto max-w-7xl space-y-6 px-4 sm:space-y-8 sm:px-6 lg:px-8">
        <EventsHeader
          filters={filters}
          resultsCount={filteredEvents.length}
          onFilterChange={handleFilterChange}
        />

        <div className="grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)] lg:gap-8 lg:items-start xl:grid-cols-[320px_minmax(0,1fr)]">
          <EventsFilters
            categories={eventCategories}
            locations={eventLocations}
            filters={filters}
            onFilterChange={handleFilterChange}
            onReset={handleReset}
          />

          <motion.div
            layout
            transition={{ duration: 0.32, ease: 'easeOut' }}
            className="min-w-0"
          >
            <EventsGrid
              events={filteredEvents}
              visibleCount={visibleCount}
              isLoading={isLoading}
              onLoadMore={handleLoadMore}
              onReset={handleReset}
            />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
