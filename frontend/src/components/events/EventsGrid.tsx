'use client';

import { AnimatePresence, motion } from 'framer-motion';
import type { EventRecord } from '@/types/eventDiscovery';
import { EventCard } from '@/components/events/EventCard';
import { EmptyState } from '@/components/events/EmptyState';
import { EventsSkeleton } from '@/components/events/EventsSkeleton';

interface EventsGridProps {
  events: EventRecord[];
  visibleCount: number;
  isLoading: boolean;
  onLoadMore: () => void;
  onReset: () => void;
}

export function EventsGrid({
  events,
  visibleCount,
  isLoading,
  onLoadMore,
  onReset,
}: EventsGridProps) {
  const visibleEvents = events.slice(0, visibleCount);
  const canLoadMore = visibleCount < events.length;

  return (
    <section className="space-y-6 sm:space-y-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#4285F4] sm:text-xs">
            Curated Selection
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-[#0D47A1] sm:text-3xl">
            Browse what is happening next
          </h2>
        </div>
        <p className="text-sm text-[#666666]">
          Showing <span className="font-semibold text-[#34A853]">{events.length}</span>{' '}
          upcoming events
        </p>
      </div>

      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <EventsSkeleton />
          </motion.div>
        ) : events.length === 0 ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <EmptyState onReset={onReset} />
          </motion.div>
        ) : (
          <motion.div
            key={`grid-${events.length}-${visibleCount}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-8"
          >
            <div className="grid gap-5 sm:gap-6 md:grid-cols-2 2xl:grid-cols-3">
              {visibleEvents.map((event, index) => (
                <EventCard key={event.id} event={event} index={index} />
              ))}
            </div>

            {canLoadMore ? (
              <div className="flex justify-center">
                <motion.button
                  type="button"
                  onClick={onLoadMore}
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  className="rounded-full border border-[#4285F4] bg-white px-6 py-3 text-sm font-medium text-[#0D47A1] shadow-[0_14px_34px_-18px_rgba(66,133,244,0.45)] transition-colors hover:bg-[#4285F4] hover:text-white"
                >
                  Load More
                </motion.button>
              </div>
            ) : null}
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
