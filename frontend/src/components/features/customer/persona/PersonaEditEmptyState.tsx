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
        className="w-full max-w-md rounded-[28px] border border-[#DCE4F2] bg-white p-8 text-center shadow-[0_24px_60px_-36px_rgba(13,71,161,0.18)]"
      >
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-[#EAF2FF]">
          <Sparkles className="h-10 w-10 text-[#4285F4]" />
        </div>

        <h1 className="mb-3 text-2xl font-bold text-[#0D47A1]">No Persona Yet</h1>
        <p className="mb-6 text-sm leading-relaxed text-[#5B6780]">
          Your preferences will appear here after you interact with the platform or create a persona. Start exploring events and vendors to build your personalized profile.
        </p>

        <button
          type="button"
          onClick={() => router.push(ROUTES.CUSTOMER.PERSONA)}
          className="inline-flex items-center gap-2 rounded-full bg-[#0D47A1] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#4285F4]"
        >
          Back to People
        </button>
      </motion.div>
    </div>
  );
}
