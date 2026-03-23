'use client';

import { motion } from 'framer-motion';

export function PersonaEditSkeleton() {
  return (
    <div>
      <div className="border-b border-[#DCE4F2] bg-white">
        <div className="mx-auto max-w-3xl px-4 py-4 sm:px-6">
          <div className="mb-3 h-4 w-32 animate-pulse rounded bg-[#E6ECF7]" />
          <div className="h-8 w-48 animate-pulse rounded bg-[#E6ECF7]" />
          <div className="mt-2 h-4 w-96 animate-pulse rounded bg-[#E6ECF7]" />
        </div>
      </div>

      <div className="mx-auto max-w-3xl px-4 pt-6 sm:px-6">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          <div className="rounded-3xl border border-[#DCE4F2] bg-white p-5 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)] sm:p-6">
            <div className="mb-5 flex items-center gap-3">
              <div className="h-10 w-10 animate-pulse rounded-full bg-[#E6ECF7]" />
              <div className="space-y-2">
                <div className="h-5 w-24 animate-pulse rounded bg-[#E6ECF7]" />
                <div className="h-4 w-40 animate-pulse rounded bg-[#E6ECF7]" />
              </div>
            </div>
            <div className="space-y-4">
              <div className="h-12 w-full animate-pulse rounded-xl bg-[#EFF4FB]" />
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="h-12 animate-pulse rounded-xl bg-[#EFF4FB]" />
                <div className="h-12 animate-pulse rounded-xl bg-[#EFF4FB]" />
              </div>
              <div className="h-12 w-full animate-pulse rounded-xl bg-[#EFF4FB]" />
            </div>
          </div>

          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-3xl border border-[#DCE4F2] bg-white p-5 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)] sm:p-6">
              <div className="mb-5 flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 animate-pulse rounded bg-[#E6ECF7]" />
                  <div className="space-y-2">
                    <div className="h-5 w-32 animate-pulse rounded bg-[#E6ECF7]" />
                    <div className="h-4 w-48 animate-pulse rounded bg-[#E6ECF7]" />
                  </div>
                </div>
                <div className="h-8 w-12 animate-pulse rounded-full bg-[#E6ECF7]" />
              </div>
              <div className="flex flex-wrap gap-2">
                {[1, 2, 3, 4, 5, 6].map((j) => (
                  <div key={j} className="h-9 w-20 animate-pulse rounded-full bg-[#EFF4FB]" />
                ))}
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
