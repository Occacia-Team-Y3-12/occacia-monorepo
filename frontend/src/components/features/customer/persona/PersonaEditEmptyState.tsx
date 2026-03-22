'use client';

import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';

export function PersonaEditEmptyState() {
  const router = useRouter();

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md text-center"
      >
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-[#f5c871]/10">
          <Sparkles className="h-10 w-10 text-[#f5c871]" />
        </div>

        <h1 className="mb-3 text-2xl font-bold text-white">No Persona Yet</h1>
        <p className="mb-6 text-sm leading-relaxed text-white/60">
          Your preferences will appear here after you interact with the platform or create a persona. Start exploring events and vendors to build your personalized profile.
        </p>

        <button
          type="button"
          onClick={() => router.push(ROUTES.CUSTOMER.DASHBOARD)}
          className="inline-flex items-center gap-2 rounded-full bg-[#f5c871] px-6 py-3 text-sm font-semibold text-[#0a0d14] transition hover:bg-[#ffe2a2]"
        >
          Go to Dashboard
        </button>
      </motion.div>
    </div>
  );
}
