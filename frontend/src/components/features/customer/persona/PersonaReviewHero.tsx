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
      className="relative overflow-hidden rounded-[36px] border border-[#DCE4F2] bg-[radial-gradient(circle_at_top,_rgba(66,133,244,0.16),_transparent_34%),linear-gradient(145deg,#FFFFFF_0%,#F5FAFF_55%,#EEF5FF_100%)] px-6 py-8 shadow-[0_24px_60px_-36px_rgba(13,71,161,0.24)] sm:px-8 sm:py-10"
    >
      <div className="absolute -right-10 top-0 h-36 w-36 rounded-full bg-[#4285F4]/12 blur-3xl" />
      <div className="absolute bottom-0 left-0 h-28 w-28 rounded-full bg-[#8ED8C7]/14 blur-3xl" />

      <div className="relative z-10 space-y-5">
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-[#D7DFEC] bg-[#F8FBFF] px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#5B6780]">
            <Sparkles className="h-3.5 w-3.5 text-[#4285F4]" />
            Almost done
          </span>
          <span className="inline-flex rounded-full border border-[#B7E4C7] bg-[#F0FBF4] px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#1F7D46]">
            Step 1 of 1
          </span>
          {isConfirmed && (
            <span className="inline-flex rounded-full border border-[#C8D7F0] bg-[#EEF5FF] px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#0D47A1]">
              Confirmed
            </span>
          )}
        </div>

        <div className="space-y-3">
          <h1 className="max-w-xl text-4xl font-semibold tracking-tight text-[#173B7A] sm:text-5xl">
            Review Your Persona
          </h1>
          <p className="max-w-2xl text-base leading-7 text-[#5B6780] sm:text-lg">
            We inferred your preferences from your conversations and event activity.
          </p>
        </div>

        <div className="max-w-2xl rounded-[28px] border border-[#D7DFEC] bg-white/85 px-4 py-4 text-sm leading-6 text-[#4A5976] sm:px-5">
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-[#0D47A1]" />
            <p>
              You can refine anything before confirming. This helps us improve future recommendations.
            </p>
          </div>
        </div>
      </div>
    </motion.section>
  );
}
