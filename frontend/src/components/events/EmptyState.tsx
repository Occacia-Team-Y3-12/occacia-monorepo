'use client';

import { motion } from 'framer-motion';

interface EmptyStateProps {
  onReset: () => void;
}

export function EmptyState({ onReset }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[28px] border border-[#EAEAEA] bg-white px-6 py-14 text-center shadow-[0_24px_70px_-34px_rgba(13,71,161,0.18)] sm:px-8 sm:py-16"
    >
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-[#EA4335] text-sm font-semibold uppercase tracking-[0.2em] text-white">
        0
      </div>
      <h3 className="text-2xl font-semibold tracking-[-0.04em] text-[#0D47A1] sm:text-3xl">
        No events match your filters
      </h3>
      <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-[#666666]">
        Try broadening your search, switching the date range, or clearing the filters
        to surface more upcoming experiences.
      </p>
      <button
        type="button"
        onClick={onReset}
        className="mt-8 inline-flex rounded-full border border-[#EA4335] bg-white px-5 py-3 text-sm font-medium text-[#EA4335] transition-colors hover:bg-[#EA4335] hover:text-white"
      >
        Reset Filters
      </button>
    </motion.div>
  );
}
