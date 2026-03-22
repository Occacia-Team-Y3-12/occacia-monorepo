'use client';

import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ChevronDown, Plus, X } from 'lucide-react';

type PersonaEditPreferenceGroupProps = {
  title: string;
  subtitle: string;
  icon: string;
  values: string[];
  suggestions: string[];
  onToggle: (value: string) => void;
  onAdd: (value: string) => void;
};

const normalize = (value: string) => value.trim().toLowerCase();

export function PersonaEditPreferenceGroup({
  title,
  subtitle,
  icon,
  values,
  suggestions,
  onToggle,
  onAdd,
}: PersonaEditPreferenceGroupProps) {
  const [customValue, setCustomValue] = useState('');
  const [showAll, setShowAll] = useState(false);

  const existingSet = new Set(values.map(normalize));
  const allOptions = [...values, ...suggestions.filter((s) => !existingSet.has(normalize(s)))];
  const visibleOptions = showAll ? allOptions : allOptions.slice(0, 12);
  const canAdd = customValue.trim() && !existingSet.has(normalize(customValue));

  const handleAdd = () => {
    if (canAdd) {
      onAdd(customValue);
      setCustomValue('');
    }
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 rounded-3xl border border-white/10 bg-[#0d1117] p-5 sm:p-6"
    >
      <div className="mb-5 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <h2 className="text-lg font-semibold text-white">{title}</h2>
            <p className="text-sm text-white/60">{subtitle}</p>
          </div>
        </div>
        <div className="rounded-full bg-[#f5c871]/10 px-3 py-1 text-sm font-semibold text-[#f5c871]">
          {values.length}
        </div>
      </div>

      <div className="mb-4 flex gap-2 rounded-xl border border-dashed border-white/10 bg-black/20 p-3">
        <input
          value={customValue}
          onChange={(e) => setCustomValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && canAdd) {
              e.preventDefault();
              handleAdd();
            }
          }}
          placeholder="Add custom preference..."
          className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-white/30"
        />
        <button
          type="button"
          onClick={handleAdd}
          disabled={!canAdd}
          className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#f5c871]/10 text-[#f5c871] transition hover:bg-[#f5c871]/20 disabled:opacity-40"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        <AnimatePresence>
          {visibleOptions.map((option) => {
            const isSelected = existingSet.has(normalize(option));
            return (
              <motion.button
                key={option}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                whileTap={{ scale: 0.95 }}
                type="button"
                onClick={() => onToggle(option)}
                className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition ${
                  isSelected
                    ? 'border-[#f5c871] bg-[#f5c871] text-[#0a0d14] shadow-lg'
                    : 'border-white/10 bg-white/5 text-white/80 hover:border-white/20 hover:bg-white/10'
                }`}
              >
                <span>{option}</span>
                {isSelected && <X className="h-3.5 w-3.5" />}
              </motion.button>
            );
          })}
        </AnimatePresence>
      </div>

      {allOptions.length > 12 && (
        <button
          type="button"
          onClick={() => setShowAll(!showAll)}
          className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-[#f5c871] transition hover:text-[#ffe2a2]"
        >
          <span>{showAll ? 'Show less' : `Show ${allOptions.length - 12} more`}</span>
          <ChevronDown className={`h-4 w-4 transition ${showAll ? 'rotate-180' : ''}`} />
        </button>
      )}
    </motion.section>
  );
}
