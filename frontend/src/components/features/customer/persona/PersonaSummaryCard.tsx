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
    <div className="rounded-[24px] border border-white/10 bg-white/[0.04] px-4 py-3">
      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-white/35">
        {icon}
        <span>{label}</span>
      </div>
      <p className="mt-2 text-sm text-white/78">{value || 'Not added yet'}</p>
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
      className="rounded-[32px] border border-white/10 bg-[linear-gradient(180deg,rgba(21,25,43,0.96),rgba(9,12,22,0.98))] p-5 shadow-[0_24px_70px_rgba(0,0,0,0.32)] sm:p-6"
    >
      <div className="flex flex-col gap-4 border-b border-white/8 pb-5 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-white/35">Identity Snapshot</p>
          <h2 className="mt-2 text-2xl font-semibold text-white sm:text-[28px]">{draft.name || 'Your persona'}</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-white/60">
            This is the profile we use to personalize recommendations, styles, and event suggestions for you.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <span
            className={`inline-flex rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] ${
              isConfirmed
                ? 'border border-[#5dd7c4]/25 bg-[#5dd7c4]/12 text-[#b8f6eb]'
                : 'border border-[#f5c871]/25 bg-[#f5c871]/10 text-[#ffe2a2]'
            }`}
          >
            {isConfirmed ? 'Confirmed' : 'Awaiting confirmation'}
          </span>
          <button
            type="button"
            onClick={isEditing ? onCancelEditing : onStartEditing}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white/80 transition hover:bg-white/10"
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
          className="mt-5 space-y-4 overflow-hidden rounded-[28px] border border-white/10 bg-white/[0.04] p-4 sm:p-5"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-white/75">Name</span>
              <input
                value={draft.name}
                onChange={(event) => onFieldChange('name', event.target.value)}
                placeholder="How should we refer to you?"
                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition placeholder:text-white/25 focus:border-[#f5c871]/50"
              />
              {validationErrors.name && <p className="text-sm text-[#ff9d9d]">{validationErrors.name}</p>}
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-white/75">Relationship</span>
              <input
                value={draft.relationship}
                onChange={(event) => onFieldChange('relationship', event.target.value)}
                placeholder="Partner, self, family, friend..."
                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition placeholder:text-white/25 focus:border-[#f5c871]/50"
              />
            </label>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium text-white/75">Birthday</span>
              <input
                type="date"
                value={draft.birthday}
                onChange={(event) => onFieldChange('birthday', event.target.value)}
                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition focus:border-[#f5c871]/50"
              />
              {validationErrors.birthday && <p className="text-sm text-[#ff9d9d]">{validationErrors.birthday}</p>}
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium text-white/75">Short personality summary</span>
              <input
                value={draft.personality}
                onChange={(event) => onFieldChange('personality', event.target.value)}
                placeholder="Warm, adventurous, detail-oriented..."
                className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition placeholder:text-white/25 focus:border-[#f5c871]/50"
              />
            </label>
          </div>
        </motion.div>
      )}
    </motion.section>
  );
}
