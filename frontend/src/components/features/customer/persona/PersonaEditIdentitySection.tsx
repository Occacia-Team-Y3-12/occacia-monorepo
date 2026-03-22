'use client';

import { motion } from 'framer-motion';
import { User } from 'lucide-react';
import { CustomerPersonaDraft } from '@/types/customer/persona';

type PersonaEditIdentitySectionProps = {
  draft: CustomerPersonaDraft;
  validationErrors: Partial<Record<'name' | 'birthday', string>>;
  onFieldChange: (field: keyof CustomerPersonaDraft, value: string) => void;
};

export function PersonaEditIdentitySection({
  draft,
  validationErrors,
  onFieldChange,
}: PersonaEditIdentitySectionProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-6 rounded-3xl border border-white/10 bg-[#0d1117] p-5 sm:p-6"
    >
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#f5c871]/10">
          <User className="h-5 w-5 text-[#f5c871]" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-white">Identity</h2>
          <p className="text-sm text-white/60">Basic information about you</p>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="mb-2 block text-sm font-medium text-white/80">
            Name <span className="text-[#ff9d9d]">*</span>
          </label>
          <input
            value={draft.name}
            onChange={(e) => onFieldChange('name', e.target.value)}
            placeholder="Your name"
            className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition placeholder:text-white/30 focus:border-[#f5c871]/50"
          />
          {validationErrors.name && (
            <p className="mt-1 text-sm text-[#ff9d9d]">{validationErrors.name}</p>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium text-white/80">Relationship</label>
            <input
              value={draft.relationship}
              onChange={(e) => onFieldChange('relationship', e.target.value)}
              placeholder="Partner, self, family..."
              className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition placeholder:text-white/30 focus:border-[#f5c871]/50"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-white/80">Birthday</label>
            <input
              type="date"
              value={draft.birthday}
              onChange={(e) => onFieldChange('birthday', e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition focus:border-[#f5c871]/50"
            />
            {validationErrors.birthday && (
              <p className="mt-1 text-sm text-[#ff9d9d]">{validationErrors.birthday}</p>
            )}
          </div>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-white/80">Personality</label>
          <input
            value={draft.personality}
            onChange={(e) => onFieldChange('personality', e.target.value)}
            placeholder="Warm, adventurous, detail-oriented..."
            className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-white outline-none transition placeholder:text-white/30 focus:border-[#f5c871]/50"
          />
        </div>
      </div>
    </motion.section>
  );
}
