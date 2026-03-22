'use client';

import { motion } from 'framer-motion';
import { ChevronDown, Radar } from 'lucide-react';

type InsightGroup = {
  label: string;
  items: string[];
};

type PersonaInsightsSectionProps = {
  insights: InsightGroup[];
  rawPreferencesJson: unknown | null;
};

export function PersonaInsightsSection({
  insights,
  rawPreferencesJson,
}: PersonaInsightsSectionProps) {
  if (!insights.length && !rawPreferencesJson) {
    return null;
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-[32px] border border-white/10 bg-[linear-gradient(180deg,rgba(17,21,36,0.96),rgba(10,14,24,0.98))] p-5 shadow-[0_24px_70px_rgba(0,0,0,0.32)] sm:p-6"
    >
      <div className="mb-5 flex items-start gap-3">
        <div className="rounded-2xl border border-[#5dd7c4]/20 bg-[#5dd7c4]/10 p-3 text-[#b8f6eb]">
          <Radar className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white sm:text-2xl">More Signals We Picked Up</h2>
          <p className="mt-1 text-sm leading-6 text-white/60">
            These extra hints came from your activity and conversations. We only surface them if they look usable.
          </p>
        </div>
      </div>

      {insights.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {insights.map((group) => (
            <div key={group.label} className="rounded-[26px] border border-white/10 bg-white/[0.04] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/35">{group.label}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {group.items.map((item) => (
                  <span
                    key={`${group.label}-${item}`}
                    className="rounded-full border border-white/10 bg-black/20 px-3 py-1.5 text-sm text-white/78"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {Boolean(rawPreferencesJson) && (
        <details className="mt-5 rounded-[24px] border border-white/10 bg-black/20 p-4 text-sm text-white/60">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 font-semibold text-white/72">
            Advanced raw data
            <ChevronDown className="h-4 w-4" />
          </summary>
          <pre className="mt-4 overflow-x-auto rounded-2xl border border-white/8 bg-[#090c15] p-4 text-xs leading-6 text-white/65">
            {JSON.stringify(rawPreferencesJson, null, 2) ?? ''}
          </pre>
        </details>
      )}
    </motion.section>
  );
}
