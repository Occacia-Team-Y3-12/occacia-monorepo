'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Code } from 'lucide-react';

type PersonaEditAdvancedSectionProps = {
  preferencesJson: unknown | null;
};

export function PersonaEditAdvancedSection({ preferencesJson }: PersonaEditAdvancedSectionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!preferencesJson) return null;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-4 rounded-3xl border border-[#DCE4F2] bg-white p-5 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)] sm:p-6"
    >
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#EAF2FF]">
            <Code className="h-5 w-5 text-[#4285F4]" />
          </div>
          <div className="text-left">
            <h2 className="text-lg font-semibold text-[#0D47A1]">Advanced Preferences</h2>
            <p className="text-sm text-[#5B6780]">Additional inferred data</p>
          </div>
        </div>
        <ChevronDown
          className={`h-5 w-5 text-[#5B6780] transition ${isExpanded ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="mt-4 overflow-hidden"
          >
            <pre className="overflow-x-auto rounded-xl border border-[#D7DFEC] bg-[#FAFBFE] p-4 text-xs text-[#4A5976]">
              {JSON.stringify(preferencesJson, null, 2)}
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
}
