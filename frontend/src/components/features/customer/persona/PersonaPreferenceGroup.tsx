'use client';

import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { PersonaChipSelector } from './PersonaChipSelector';

type PersonaPreferenceGroupProps = {
  title: string;
  caption: string;
  values: string[];
  suggestions: string[];
  searchValue: string;
  draftValue: string;
  onSearchChange: (value: string) => void;
  onDraftValueChange: (value: string) => void;
  onToggle: (value: string) => void;
  onAdd: (value: string) => void;
  expanded: boolean;
  onToggleExpanded: () => void;
  accentClassName?: string;
};

export function PersonaPreferenceGroup({
  title,
  caption,
  values,
  suggestions,
  searchValue,
  draftValue,
  onSearchChange,
  onDraftValueChange,
  onToggle,
  onAdd,
  expanded,
  onToggleExpanded,
  accentClassName,
}: PersonaPreferenceGroupProps) {
  return (
    <motion.section
      layout
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[32px] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(245,200,113,0.14),_transparent_35%),linear-gradient(180deg,rgba(17,20,35,0.95),rgba(12,15,27,0.98))] p-5 shadow-[0_24px_70px_rgba(0,0,0,0.32)] sm:p-6"
    >
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-white/55">
            <Sparkles className="h-3.5 w-3.5 text-[#f5c871]" />
            Preference Group
          </div>
          <h2 className="text-xl font-semibold text-white sm:text-2xl">{title}</h2>
          <p className="mt-1 text-sm leading-6 text-white/60">{caption}</p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-2 text-right">
          <p className="text-[11px] uppercase tracking-[0.18em] text-white/35">Selected</p>
          <p className="mt-1 text-lg font-semibold text-white">{values.length}</p>
        </div>
      </div>

      <PersonaChipSelector
        title={title}
        values={values}
        suggestions={suggestions}
        searchValue={searchValue}
        draftValue={draftValue}
        onSearchChange={onSearchChange}
        onDraftValueChange={onDraftValueChange}
        onToggle={onToggle}
        onAdd={onAdd}
        expanded={expanded}
        onToggleExpanded={onToggleExpanded}
        accentClassName={accentClassName}
      />
    </motion.section>
  );
}
