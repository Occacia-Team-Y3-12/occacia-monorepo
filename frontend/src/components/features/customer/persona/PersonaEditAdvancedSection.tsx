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
      className="mt-4 rounded-3xl border border-white/10 bg-[#0d1117] p-5 sm:p-6"
    >
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/5">
            <Code className="h-5 w-5 text-white/60" />
          </div>
          <div className="text-left">
            <h2 className="text-lg font-semibold text-white">Advanced Preferences</h2>
            <p className="text-sm text-white/60">Additional inferred data</p>
          </div>
        </div>
        <ChevronDown
          className={`h-5 w-5 text-white/60 transition ${isExpanded ? 'rotate-180' : ''}`}
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
            <pre className="overflow-x-auto rounded-xl border border-white/10 bg-black/40 p-4 text-xs text-white/70">
              {JSON.stringify(preferencesJson, null, 2)}
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
}
