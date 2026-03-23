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
      className="mt-4 rounded-3xl border border-[#DCE4F2] bg-white p-5 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)] sm:p-6"
    >
      <div className="mb-5 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{icon}</span>
          <div>
            <h2 className="text-lg font-semibold text-[#0D47A1]">{title}</h2>
            <p className="text-sm text-[#5B6780]">{subtitle}</p>
          </div>
        </div>
        <div className="rounded-full bg-[#EAF2FF] px-3 py-1 text-sm font-semibold text-[#0D47A1]">
          {values.length}
        </div>
      </div>

      <div className="mb-4 flex gap-2 rounded-xl border border-dashed border-[#D7DFEC] bg-[#FAFBFE] p-3">
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
          className="flex-1 bg-transparent text-sm text-[#24324A] outline-none placeholder:text-[#8A96AE]"
        />
        <button
          type="button"
          onClick={handleAdd}
          disabled={!canAdd}
          className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#EAF2FF] text-[#0D47A1] transition hover:bg-[#D7E7FF] disabled:opacity-40"
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
                    ? 'border-[#4285F4] bg-[#EAF2FF] text-[#0D47A1] shadow-[0_12px_24px_-18px_rgba(13,71,161,0.5)]'
                    : 'border-[#D7DFEC] bg-[#F8FBFF] text-[#4A5976] hover:border-[#BFD0EE] hover:bg-[#F1F6FE]'
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
          className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-[#0D47A1] transition hover:text-[#4285F4]"
        >
          <span>{showAll ? 'Show less' : `Show ${allOptions.length - 12} more`}</span>
          <ChevronDown className={`h-4 w-4 transition ${showAll ? 'rotate-180' : ''}`} />
        </button>
      )}
    </motion.section>
  );
}
