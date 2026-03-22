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
      className="sticky bottom-4 z-20 rounded-[24px] border border-[#DCE4F2] bg-white/95 px-5 py-4 shadow-[0_20px_48px_-32px_rgba(13,71,161,0.28)] backdrop-blur"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-[#173B7A]">
            {isConfirmed ? 'Your persona is confirmed.' : 'Ready when this feels like you.'}
          </p>
          <p className="mt-1 text-sm text-[#5B6780]">
            {isDirty
              ? 'We will save your edits before confirming.'
              : 'You can still refine these preferences later.'}
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <button
            type="button"
            onClick={onEdit}
            className="inline-flex items-center justify-center gap-2 rounded-full border border-[#D7DFEC] bg-[#F8FBFF] px-5 py-3 text-sm font-semibold text-[#35548D] transition hover:border-[#BFD0EE] hover:bg-[#EEF5FF]"
          >
            <PencilLine className="h-4 w-4" />
            Edit details
          </button>

          <button
            type="button"
            onClick={onSkip}
            className="inline-flex items-center justify-center gap-2 rounded-full border border-[#D7DFEC] bg-transparent px-5 py-3 text-sm font-semibold text-[#5B6780] transition hover:bg-[#F8FBFF]"
          >
            <SkipForward className="h-4 w-4" />
            Skip for now
          </button>

          <button
            type="button"
            onClick={onConfirm}
            disabled={isSaving || isConfirming}
            className="inline-flex items-center justify-center gap-2 rounded-full bg-[#0D47A1] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#1C5BC3] disabled:cursor-not-allowed disabled:opacity-60"
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
