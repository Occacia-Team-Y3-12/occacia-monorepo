'use client';

import { motion } from 'framer-motion';

export function PersonaEditSkeleton() {
  return (
    <div>
      <div className="border-b border-white/10 bg-[#0d1117]">
        <div className="mx-auto max-w-3xl px-4 py-4 sm:px-6">
          <div className="mb-3 h-4 w-32 animate-pulse rounded bg-white/10" />
          <div className="h-8 w-48 animate-pulse rounded bg-white/10" />
          <div className="mt-2 h-4 w-96 animate-pulse rounded bg-white/10" />
        </div>
      </div>

      <div className="mx-auto max-w-3xl px-4 pt-6 sm:px-6">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          <div className="rounded-3xl border border-white/10 bg-[#0d1117] p-5 sm:p-6">
            <div className="mb-5 flex items-center gap-3">
              <div className="h-10 w-10 animate-pulse rounded-full bg-white/10" />
              <div className="space-y-2">
                <div className="h-5 w-24 animate-pulse rounded bg-white/10" />
                <div className="h-4 w-40 animate-pulse rounded bg-white/10" />
              </div>
            </div>
            <div className="space-y-4">
              <div className="h-12 w-full animate-pulse rounded-xl bg-white/10" />
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="h-12 animate-pulse rounded-xl bg-white/10" />
                <div className="h-12 animate-pulse rounded-xl bg-white/10" />
              </div>
              <div className="h-12 w-full animate-pulse rounded-xl bg-white/10" />
            </div>
          </div>

          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-3xl border border-white/10 bg-[#0d1117] p-5 sm:p-6">
              <div className="mb-5 flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 animate-pulse rounded bg-white/10" />
                  <div className="space-y-2">
                    <div className="h-5 w-32 animate-pulse rounded bg-white/10" />
                    <div className="h-4 w-48 animate-pulse rounded bg-white/10" />
                  </div>
                </div>
                <div className="h-8 w-12 animate-pulse rounded-full bg-white/10" />
              </div>
              <div className="flex flex-wrap gap-2">
                {[1, 2, 3, 4, 5, 6].map((j) => (
                  <div key={j} className="h-9 w-20 animate-pulse rounded-full bg-white/10" />
                ))}
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
