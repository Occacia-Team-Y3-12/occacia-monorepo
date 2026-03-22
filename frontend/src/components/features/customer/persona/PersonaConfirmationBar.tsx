'use client';

import { motion } from 'framer-motion';
import { Check, Loader2, PencilLine, SkipForward } from 'lucide-react';

type PersonaConfirmationBarProps = {
  isConfirmed: boolean;
  isDirty: boolean;
  isSaving: boolean;
  isConfirming: boolean;
  onConfirm: () => void;
  onSkip: () => void;
  onEdit: () => void;
};

export function PersonaConfirmationBar({
  isConfirmed,
  isDirty,
  isSaving,
  isConfirming,
  onConfirm,
  onSkip,
  onEdit,
}: PersonaConfirmationBarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky bottom-4 z-20 rounded-[28px] border border-white/10 bg-[#0e1220]/92 p-4 shadow-[0_22px_60px_rgba(0,0,0,0.45)] backdrop-blur"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-white">
            {isConfirmed ? 'Your persona is confirmed.' : 'Ready when this feels like you.'}
          </p>
          <p className="mt-1 text-sm text-white/55">
            {isDirty
              ? 'We will save your edits before confirming.'
              : 'You can still refine these preferences later.'}
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={onEdit}
            className="inline-flex items-center justify-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white/78 transition hover:bg-white/10"
          >
            <PencilLine className="h-4 w-4" />
            Edit details
          </button>

          <button
            type="button"
            onClick={onSkip}
            className="inline-flex items-center justify-center gap-2 rounded-full border border-white/10 bg-transparent px-4 py-3 text-sm font-semibold text-white/72 transition hover:bg-white/6"
          >
            <SkipForward className="h-4 w-4" />
            Skip for now
          </button>

          <button
            type="button"
            onClick={onConfirm}
            disabled={isSaving || isConfirming}
            className="inline-flex items-center justify-center gap-2 rounded-full bg-[#f5c871] px-5 py-3 text-sm font-semibold text-[#171a23] transition hover:bg-[#ffd987] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSaving || isConfirming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Check className="h-4 w-4" />
            )}
            {isConfirmed ? 'Confirm again' : 'Confirm Persona'}
          </button>
        </div>
      </div>
    </motion.div>
  );
}
