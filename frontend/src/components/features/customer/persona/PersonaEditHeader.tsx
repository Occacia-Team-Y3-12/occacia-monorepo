'use client';

import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { ROUTES } from '@/lib/routes';

export function PersonaEditHeader() {
  const router = useRouter();

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="border-b border-white/10 bg-[#0d1117]"
    >
      <div className="mx-auto max-w-3xl px-4 py-4 sm:px-6">
        <button
          type="button"
          onClick={() => router.push(ROUTES.CUSTOMER.DASHBOARD)}
          className="mb-3 inline-flex items-center gap-2 text-sm text-white/60 transition hover:text-white/90"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </button>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">My Preferences</h1>
        <p className="mt-2 text-sm text-white/60">
          Update the preferences we use to personalize your recommendations
        </p>
        <p className="mt-1 text-xs text-white/40">
          These can be changed anytime to refine your experience
        </p>
      </div>
    </motion.header>
  );
}
