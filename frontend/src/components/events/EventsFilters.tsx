'use client';

import { motion } from 'framer-motion';
import { CalendarRange, MapPinned, Sparkles, Ticket } from 'lucide-react';
import type {
  EventCategory,
  EventDateFilter,
  EventFiltersState,
  EventPriceType,
} from '@/types/eventDiscovery';

interface EventsFiltersProps {
  categories: readonly ('all' | EventCategory)[];
  locations: string[];
  filters: EventFiltersState;
  onFilterChange: <K extends keyof EventFiltersState>(
    key: K,
    value: EventFiltersState[K],
  ) => void;
  onReset: () => void;
}

const dateOptions: { label: string; value: EventDateFilter }[] = [
  { label: 'Any Date', value: 'all' },
  { label: 'This Week', value: 'week' },
  { label: 'This Month', value: 'month' },
  { label: 'Next 3 Months', value: 'quarter' },
];

const priceOptions: { label: string; value: 'all' | EventPriceType }[] = [
  { label: 'All Prices', value: 'all' },
  { label: 'Free', value: 'Free' },
  { label: 'Paid', value: 'Paid' },
];

function selectClassName() {
  return 'h-12 w-full rounded-2xl border border-[#CCCCCC] bg-[#FAFAFA] px-4 py-3 text-sm text-[#0D47A1] outline-none transition focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20';
}

export function EventsFilters({
  categories,
  locations,
  filters,
  onFilterChange,
  onReset,
}: EventsFiltersProps) {
  return (
    <motion.aside
      initial={{ opacity: 0, x: 18 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.45, ease: 'easeOut', delay: 0.12 }}
      className="lg:sticky lg:top-24 lg:h-fit"
    >
      <div className="overflow-hidden rounded-[24px] border border-[#EAEAEA] bg-white p-4 shadow-[0_20px_60px_-34px_rgba(13,71,161,0.22)] sm:rounded-[28px] sm:p-5">
        <div className="flex items-center justify-between gap-4 border-b border-[#EAEAEA] pb-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#4285F4] sm:text-xs">
              Refine Results
            </p>
            <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-[#0D47A1]">
              Filters
            </h2>
          </div>
          <button
            type="button"
            onClick={onReset}
            className="rounded-full border border-[#CCCCCC] px-4 py-2 text-sm font-medium text-[#666666] transition hover:border-[#EA4335] hover:text-[#EA4335]"
          >
            Reset
          </button>
        </div>

        <div className="mt-5 space-y-5">
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-[#666666] sm:text-xs">
              <Sparkles className="h-3.5 w-3.5 text-[#4285F4]" />
              Category
            </label>
            <select
              value={filters.category}
              onChange={(event) =>
                onFilterChange('category', event.target.value as EventFiltersState['category'])
              }
              className={selectClassName()}
            >
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : category}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-[#666666] sm:text-xs">
              <CalendarRange className="h-3.5 w-3.5 text-[#FBBC05]" />
              Date
            </label>
            <select
              value={filters.date}
              onChange={(event) =>
                onFilterChange('date', event.target.value as EventFiltersState['date'])
              }
              className={selectClassName()}
            >
              {dateOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-[#666666] sm:text-xs">
              <MapPinned className="h-3.5 w-3.5 text-[#34A853]" />
              Location
            </label>
            <select
              value={filters.location}
              onChange={(event) => onFilterChange('location', event.target.value)}
              className={selectClassName()}
            >
              {locations.map((location) => (
                <option key={location} value={location}>
                  {location === 'all' ? 'All Locations' : location}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            <label className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-[#666666] sm:text-xs">
              <Ticket className="h-3.5 w-3.5 text-[#EA4335]" />
              Price
            </label>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              {priceOptions.map((option) => {
                const isActive = filters.priceType === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => onFilterChange('priceType', option.value)}
                    className={`rounded-2xl px-3 py-3 text-sm font-medium transition ${
                      isActive
                        ? 'border border-[#4285F4] bg-[#4285F4] text-white shadow-[0_14px_28px_-16px_rgba(66,133,244,0.65)]'
                        : 'border border-[#EAEAEA] bg-[#F4F8FA] text-[#666666] hover:border-[#34A853] hover:text-[#0D47A1]'
                    }`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}
