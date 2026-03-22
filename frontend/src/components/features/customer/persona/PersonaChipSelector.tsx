'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { Plus, Search, X } from 'lucide-react';

type PersonaChipSelectorProps = {
  title: string;
  values: string[];
  suggestions: string[];
  searchValue: string;
  draftValue: string;
  onSearchChange: (value: string) => void;
  onDraftValueChange: (value: string) => void;
  onToggle: (value: string) => void;
  onAdd: (value: string) => void;
  maxVisible?: number;
  expanded: boolean;
  onToggleExpanded: () => void;
  accentClassName?: string;
};

const normalize = (value: string) => value.trim().toLowerCase();

export function PersonaChipSelector({
  title,
  values,
  suggestions,
  searchValue,
  draftValue,
  onSearchChange,
  onDraftValueChange,
  onToggle,
  onAdd,
  maxVisible = 10,
  expanded,
  onToggleExpanded,
  accentClassName = 'from-[#f2c94c]/30 via-[#f97316]/20 to-transparent',
}: PersonaChipSelectorProps) {
  const existingSet = new Set(values.map(normalize));
  const orderedSuggestions = [
    ...values,
    ...suggestions.filter((item) => !existingSet.has(normalize(item))),
  ];

  const filteredSuggestions = orderedSuggestions.filter((item) =>
    normalize(item).includes(normalize(searchValue))
  );

  const visibleSuggestions = expanded ? filteredSuggestions : filteredSuggestions.slice(0, maxVisible);
  const canShowToggle = filteredSuggestions.length > maxVisible;
  const canAddDraft = Boolean(draftValue.trim()) && !existingSet.has(normalize(draftValue));

  return (
    <div className="space-y-4">
      <div className={`rounded-[28px] border border-[#D7DFEC] bg-gradient-to-br ${accentClassName} p-[1px]`}>
        <div className="rounded-[27px] bg-[#F8FBFF] p-4">
          <div className="flex items-center gap-3 rounded-2xl border border-[#D7DFEC] bg-white px-4 py-3">
            <Search className="h-4 w-4 text-[#7A87A3]" />
            <input
              value={searchValue}
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder={`Search ${title.toLowerCase()}`}
              className="w-full bg-transparent text-sm text-[#173B7A] placeholder:text-[#9AA6BF] focus:outline-none"
            />
          </div>

          <div className="mt-3 flex items-center gap-2 rounded-2xl border border-dashed border-[#C8D7F0] bg-white px-3 py-2.5">
            <Plus className="h-4 w-4 text-[#4285F4]" />
            <input
              value={draftValue}
              onChange={(event) => onDraftValueChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && canAddDraft) {
                  event.preventDefault();
                  onAdd(draftValue);
                }
              }}
              placeholder={`Add a custom ${title.toLowerCase()} tag`}
              className="w-full bg-transparent text-sm text-[#173B7A] placeholder:text-[#9AA6BF] focus:outline-none"
            />
            <button
              type="button"
              onClick={() => onAdd(draftValue)}
              disabled={!canAddDraft}
              className="rounded-full bg-[#0D47A1] px-3 py-1 text-xs font-semibold text-white transition hover:bg-[#1C5BC3] disabled:cursor-not-allowed disabled:opacity-40"
            >
              Add
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2.5">
        <AnimatePresence initial={false}>
          {visibleSuggestions.map((item) => {
            const active = existingSet.has(normalize(item));

            return (
              <motion.button
                key={`${title}-${item}`}
                layout
                type="button"
                whileTap={{ scale: 0.96 }}
                onClick={() => onToggle(item)}
                className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition ${
                  active
                    ? 'border-[#0D47A1] bg-[#0D47A1] text-white shadow-[0_8px_20px_rgba(13,71,161,0.2)]'
                    : 'border-[#D7DFEC] bg-white text-[#35548D] hover:border-[#BFD0EE] hover:bg-[#EEF5FF]'
                }`}
              >
                <span>{item}</span>
                {active && <X className="h-3.5 w-3.5" />}
              </motion.button>
            );
          })}
        </AnimatePresence>
      </div>

      {filteredSuggestions.length === 0 && (
        <div className="rounded-2xl border border-dashed border-[#C8D7F0] bg-[#F8FBFF] px-4 py-4 text-sm text-[#5B6780]">
          No matching suggestions right now. Add your own chip above.
        </div>
      )}

      {canShowToggle && (
        <button
          type="button"
          onClick={onToggleExpanded}
          className="text-sm font-semibold text-[#0D47A1] transition hover:text-[#1C5BC3]"
        >
          {expanded ? 'Show less' : `Show more (${filteredSuggestions.length - visibleSuggestions.length} more)`}
        </button>
      )}
    </div>
  );
}
