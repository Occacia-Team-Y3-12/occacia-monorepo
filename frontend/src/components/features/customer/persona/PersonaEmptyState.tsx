'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { ROUTES } from '@/lib/routes';

export function PersonaEmptyState() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex min-h-[65vh] flex-col items-center justify-center rounded-[36px] border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(93,215,196,0.12),_transparent_26%),linear-gradient(180deg,#101423,#0a0d17)] px-6 py-12 text-center shadow-[0_30px_80px_rgba(0,0,0,0.45)]"
    >
      <div className="rounded-[28px] border border-[#f5c871]/20 bg-[#f5c871]/10 p-4 text-[#ffe2a2]">
        <Sparkles className="h-8 w-8" />
      </div>
      <h1 className="mt-6 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
        Your persona is still taking shape
      </h1>
      <p className="mt-4 max-w-xl text-base leading-7 text-white/65">
        Persona insights will appear after more conversations, event planning activity, and recommendation feedback.
      </p>
      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        <Link
          href={ROUTES.CUSTOMER.EVENTS}
          className="rounded-full bg-[#f5c871] px-5 py-3 text-sm font-semibold text-[#171a23] transition hover:bg-[#ffd987]"
        >
          Explore events
        </Link>
        <Link
          href={ROUTES.CUSTOMER.DASHBOARD}
          className="rounded-full border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-white/78 transition hover:bg-white/10"
        >
          Back to dashboard
        </Link>
      </div>
    </motion.section>
  );
}
