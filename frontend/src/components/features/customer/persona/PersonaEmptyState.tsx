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
      className="flex min-h-[65vh] flex-col items-center justify-center rounded-[36px] border border-[#DCE4F2] bg-[radial-gradient(circle_at_top,_rgba(66,133,244,0.14),_transparent_30%),linear-gradient(180deg,#FFFFFF,#F4F8FA)] px-6 py-12 text-center shadow-[0_24px_60px_-36px_rgba(13,71,161,0.2)]"
    >
      <div className="rounded-[28px] border border-[#C8D7F0] bg-[#EEF5FF] p-4 text-[#0D47A1]">
        <Sparkles className="h-8 w-8" />
      </div>
      <h1 className="mt-6 text-3xl font-semibold tracking-tight text-[#173B7A] sm:text-4xl">
        Your persona is still taking shape
      </h1>
      <p className="mt-4 max-w-xl text-base leading-7 text-[#5B6780]">
        Persona insights will appear after more conversations, event planning activity, and recommendation feedback.
      </p>
      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        <Link
          href={ROUTES.CUSTOMER.EVENTS}
          className="rounded-full bg-[#0D47A1] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#1C5BC3]"
        >
          Explore events
        </Link>
        <Link
          href={ROUTES.CUSTOMER.DASHBOARD}
          className="rounded-full border border-[#D7DFEC] bg-[#F8FBFF] px-5 py-3 text-sm font-semibold text-[#35548D] transition hover:border-[#BFD0EE] hover:bg-[#EEF5FF]"
        >
          Back to dashboard
        </Link>
      </div>
    </motion.section>
  );
}
