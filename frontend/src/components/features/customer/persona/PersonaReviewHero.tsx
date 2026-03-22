'use client';

import { motion } from 'framer-motion';
import { ShieldCheck, Sparkles } from 'lucide-react';

type PersonaReviewHeroProps = {
  isConfirmed: boolean;
};

export function PersonaReviewHero({ isConfirmed }: PersonaReviewHeroProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative overflow-hidden rounded-[36px] border border-white/10 bg-[radial-gradient(circle_at_top,_rgba(245,200,113,0.22),_transparent_32%),linear-gradient(160deg,#15192b_0%,#0b0e18_55%,#111524_100%)] px-6 py-8 shadow-[0_30px_80px_rgba(0,0,0,0.45)] sm:px-8 sm:py-10"
    >
      <div className="absolute -right-10 top-0 h-36 w-36 rounded-full bg-[#f5c871]/12 blur-3xl" />
      <div className="absolute bottom-0 left-0 h-28 w-28 rounded-full bg-[#5dd7c4]/10 blur-3xl" />

      <div className="relative z-10 space-y-5">
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/6 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.22em] text-white/65">
            <Sparkles className="h-3.5 w-3.5 text-[#f5c871]" />
            Almost done
          </span>
          <span className="inline-flex rounded-full border border-[#5dd7c4]/20 bg-[#5dd7c4]/10 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#b8f6eb]">
            Step 1 of 1
          </span>
          {isConfirmed && (
            <span className="inline-flex rounded-full border border-[#f5c871]/25 bg-[#f5c871]/10 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#ffe2a2]">
              Confirmed
            </span>
          )}
        </div>

        <div className="space-y-3">
          <h1 className="max-w-xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
            Review Your Persona
          </h1>
          <p className="max-w-2xl text-base leading-7 text-white/72 sm:text-lg">
            We inferred your preferences from your conversations and event activity.
          </p>
        </div>

        <div className="max-w-2xl rounded-[28px] border border-white/10 bg-white/[0.05] px-4 py-4 text-sm leading-6 text-white/70 sm:px-5">
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-[#f5c871]" />
            <p>
              You can refine anything before confirming. This helps us improve future recommendations.
            </p>
          </div>
        </div>
      </div>
    </motion.section>
  );
}
