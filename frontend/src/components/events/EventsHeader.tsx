'use client';

import { motion } from 'framer-motion';
import { ArrowUpDown, Search } from 'lucide-react';
import type { EventFiltersState } from '@/types/eventDiscovery';

interface EventsHeaderProps {
  filters: EventFiltersState;
  resultsCount: number;
  onFilterChange: <K extends keyof EventFiltersState>(
    key: K,
    value: EventFiltersState[K],
  ) => void;
}

const sortOptions: { label: string; value: EventFiltersState['sort'] }[] = [
  { label: 'Newest', value: 'newest' },
  { label: 'Upcoming Soon', value: 'upcoming' },
  { label: 'Most Popular', value: 'popular' },
];

export function EventsHeader({
  filters,
  resultsCount,
  onFilterChange,
}: EventsHeaderProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="relative overflow-hidden rounded-[28px] border border-[#EAEAEA] bg-[linear-gradient(135deg,rgba(244,248,250,0.98),rgba(255,255,255,0.96))] p-5 shadow-[0_24px_70px_-34px_rgba(13,71,161,0.28)] sm:rounded-[32px] sm:p-8"
    >
      <div className="absolute inset-x-0 top-0 h-1 bg-[linear-gradient(90deg,#0D47A1,#4285F4,#34A853,#FBBC05)]" />
      <div className="absolute -left-10 top-0 h-36 w-36 rounded-full bg-[#4285F4]/14 blur-3xl sm:h-52 sm:w-52" />
      <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-[#34A853]/12 blur-3xl sm:h-56 sm:w-56" />
      <div className="absolute bottom-0 right-12 h-28 w-28 rounded-full bg-[#FBBC05]/14 blur-3xl sm:h-40 sm:w-40" />

      <div className="relative grid gap-6 xl:grid-cols-[1.12fr_0.88fr] xl:items-end">
        <div className="max-w-3xl">
          <p className="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#4285F4] sm:text-xs">
            Discover Experiences
          </p>
          <h1 className="mt-3 max-w-2xl text-4xl font-semibold tracking-[-0.06em] text-[#0D47A1] sm:mt-4 sm:text-5xl xl:text-6xl">
            All Events
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-7 text-[#666666] sm:text-base lg:text-lg">
            Browse a refined lineup of upcoming gatherings, workshops, and cultural
            moments curated for people who want more than a crowded calendar.
          </p>
          <p className="mt-5 text-sm font-medium text-[#666666]">
            <span className="text-[#0D47A1]">{resultsCount}</span> events available right now
          </p>
        </div>

        <div className="grid gap-3 rounded-[24px] border border-[#EAEAEA] bg-white/95 p-3 shadow-[0_16px_40px_-26px_rgba(13,71,161,0.22)] sm:grid-cols-[1fr_auto] sm:gap-4 sm:p-4">
          <label className="relative block">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#4285F4]" />
            <input
              type="search"
              value={filters.query}
              onChange={(event) => onFilterChange('query', event.target.value)}
              placeholder="Search by title or vibe"
              className="h-12 w-full rounded-2xl border border-[#CCCCCC] bg-[#FAFAFA] py-3 pl-11 pr-4 text-sm text-[#0D47A1] outline-none transition placeholder:text-[#666666]/80 focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20 sm:h-[52px]"
            />
          </label>

          <label className="flex h-12 items-center gap-3 rounded-2xl border border-[#CCCCCC] bg-[#FAFAFA] px-4 py-3 text-sm text-[#666666] sm:h-[52px] sm:min-w-[210px]">
            <ArrowUpDown className="h-4 w-4 text-[#34A853]" />
            <select
              value={filters.sort}
              onChange={(event) =>
                onFilterChange('sort', event.target.value as EventFiltersState['sort'])
              }
              className="w-full bg-transparent font-medium text-[#0D47A1] outline-none"
              aria-label="Sort events"
            >
              {sortOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>
    </motion.section>
  );
}
