'use client';

import { motion } from 'framer-motion';
import { CalendarDays, CheckCircle2, Edit3, HeartHandshake, UserRound } from 'lucide-react';
import { CustomerPersonaDraft } from '@/types/customer/persona';

type PersonaSummaryCardProps = {
  draft: CustomerPersonaDraft;
  isConfirmed: boolean;
  lastUpdatedLabel: string | null;
  confirmedLabel: string | null;
  isEditing: boolean;
  validationErrors: Partial<Record<'name' | 'birthday', string>>;
  onStartEditing: () => void;
  onCancelEditing: () => void;
  onFieldChange: (field: keyof CustomerPersonaDraft, value: string) => void;
};

type DetailPillProps = {
  icon: React.ReactNode;
  label: string;
  value: string;
};

function DetailPill({ icon, label, value }: DetailPillProps) {
  return (
    <div className="rounded-[24px] border border-[#DCE4F2] bg-[#F8FBFF] px-4 py-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-[#7A87A3]">
        {icon}
        <span>{label}</span>
      </div>
      <p className="mt-2 text-sm text-[#173B7A]">{value || 'Not added yet'}</p>
    </div>
  );
}

export function PersonaSummaryCard({
  draft,
  isConfirmed,
  lastUpdatedLabel,
  confirmedLabel,
  isEditing,
  validationErrors,
  onStartEditing,
  onCancelEditing,
  onFieldChange,
}: PersonaSummaryCardProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[32px] border border-[#DCE4F2] bg-white p-5 shadow-[0_24px_60px_-36px_rgba(13,71,161,0.2)] sm:p-6"
    >
      <div className="flex flex-col gap-4 border-b border-[#E6EDF8] pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#7A87A3]">Identity Snapshot</p>
          <h2 className="mt-2 text-2xl font-semibold text-[#173B7A] sm:text-[28px]">{draft.name || 'Your persona'}</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-[#5B6780]">
            This is the profile we use to personalize recommendations, styles, and event suggestions for you.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`inline-flex rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] ${
              isConfirmed
                ? 'border border-[#B7E4C7] bg-[#F0FBF4] text-[#1F7D46]'
                : 'border border-[#C8D7F0] bg-[#EEF5FF] text-[#0D47A1]'
            }`}
          >
            {isConfirmed ? 'Confirmed' : 'Awaiting confirmation'}
          </span>
          <button
            type="button"
            onClick={isEditing ? onCancelEditing : onStartEditing}
            className="inline-flex items-center gap-2 rounded-full border border-[#D7DFEC] bg-[#F8FBFF] px-4 py-2 text-sm font-semibold text-[#35548D] transition hover:border-[#BFD0EE] hover:bg-[#EEF5FF]"
          >
            <Edit3 className="h-4 w-4" />
            {isEditing ? 'Done editing' : 'Edit details'}
          </button>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <DetailPill
          icon={<HeartHandshake className="h-3.5 w-3.5 text-[#f5c871]" />}
          label="Relationship"
          value={draft.relationship}
        />
        <DetailPill
          icon={<CalendarDays className="h-3.5 w-3.5 text-[#f5c871]" />}
          label="Birthday"
          value={draft.birthday}
        />
        <DetailPill
          icon={<UserRound className="h-3.5 w-3.5 text-[#f5c871]" />}
          label="Personality"
          value={draft.personality}
        />
        <DetailPill
          icon={<CheckCircle2 className="h-3.5 w-3.5 text-[#f5c871]" />}
          label="Timeline"
          value={confirmedLabel || lastUpdatedLabel || 'Freshly inferred'}
        />
      </div>

      {isEditing && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-5 space-y-4 overflow-hidden rounded-[28px] border border-[#DCE4F2] bg-[#F8FBFF] p-4 sm:p-5"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-[#4A5976]">Name</span>
              <input
                value={draft.name}
                onChange={(event) => onFieldChange('name', event.target.value)}
                placeholder="How should we refer to you?"
                className="w-full rounded-2xl border border-[#D7DFEC] bg-white px-4 py-3 text-[#173B7A] outline-none transition placeholder:text-[#9AA6BF] focus:border-[#4285F4]"
              />
              {validationErrors.name && <p className="text-sm text-[#ff9d9d]">{validationErrors.name}</p>}
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-[#4A5976]">Relationship</span>
              <input
                value={draft.relationship}
                onChange={(event) => onFieldChange('relationship', event.target.value)}
                placeholder="Partner, self, family, friend..."
                className="w-full rounded-2xl border border-[#D7DFEC] bg-white px-4 py-3 text-[#173B7A] outline-none transition placeholder:text-[#9AA6BF] focus:border-[#4285F4]"
              />
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-[#4A5976]">Birthday</span>
              <input
                type="date"
                value={draft.birthday}
                onChange={(event) => onFieldChange('birthday', event.target.value)}
                className="w-full rounded-2xl border border-[#D7DFEC] bg-white px-4 py-3 text-[#173B7A] outline-none transition focus:border-[#4285F4]"
              />
              {validationErrors.birthday && <p className="text-sm text-[#ff9d9d]">{validationErrors.birthday}</p>}
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-[#4A5976]">Short personality summary</span>
              <input
                value={draft.personality}
                onChange={(event) => onFieldChange('personality', event.target.value)}
                placeholder="Warm, adventurous, detail-oriented..."
                className="w-full rounded-2xl border border-[#D7DFEC] bg-white px-4 py-3 text-[#173B7A] outline-none transition placeholder:text-[#9AA6BF] focus:border-[#4285F4]"
              />
            </label>
          </div>
        </motion.div>
      )}
    </motion.section>
  );
}
