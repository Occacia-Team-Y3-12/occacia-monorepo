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
      className="mt-6 rounded-3xl border border-[#DCE4F2] bg-white p-5 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)] sm:p-6"
    >
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#EAF2FF]">
          <User className="h-5 w-5 text-[#4285F4]" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-[#0D47A1]">Identity</h2>
          <p className="text-sm text-[#5B6780]">Basic information about you</p>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="mb-2 block text-sm font-medium text-[#4A5976]">
            Name <span className="text-[#B23C3C]">*</span>
          </label>
          <input
            value={draft.name}
            onChange={(e) => onFieldChange('name', e.target.value)}
            placeholder="Your name"
            className="w-full rounded-xl border border-[#D7DFEC] bg-[#FAFBFE] px-4 py-3 text-[#24324A] outline-none transition placeholder:text-[#8A96AE] focus:border-[#4285F4]"
          />
          {validationErrors.name && (
            <p className="mt-1 text-sm text-[#B23C3C]">{validationErrors.name}</p>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium text-[#4A5976]">Relationship</label>
            <input
              value={draft.relationship}
              onChange={(e) => onFieldChange('relationship', e.target.value)}
              placeholder="Partner, self, family..."
              className="w-full rounded-xl border border-[#D7DFEC] bg-[#FAFBFE] px-4 py-3 text-[#24324A] outline-none transition placeholder:text-[#8A96AE] focus:border-[#4285F4]"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-[#4A5976]">Birthday</label>
            <input
              type="date"
              value={draft.birthday}
              onChange={(e) => onFieldChange('birthday', e.target.value)}
              className="w-full rounded-xl border border-[#D7DFEC] bg-[#FAFBFE] px-4 py-3 text-[#24324A] outline-none transition focus:border-[#4285F4]"
            />
            {validationErrors.birthday && (
              <p className="mt-1 text-sm text-[#B23C3C]">{validationErrors.birthday}</p>
            )}
          </div>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-[#4A5976]">Personality</label>
          <input
            value={draft.personality}
            onChange={(e) => onFieldChange('personality', e.target.value)}
            placeholder="Warm, adventurous, detail-oriented..."
            className="w-full rounded-xl border border-[#D7DFEC] bg-[#FAFBFE] px-4 py-3 text-[#24324A] outline-none transition placeholder:text-[#8A96AE] focus:border-[#4285F4]"
          />
        </div>
      </div>
    </motion.section>
  );
}
