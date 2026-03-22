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
      className="rounded-[32px] border border-[#DCE4F2] bg-white p-5 shadow-[0_24px_60px_-36px_rgba(13,71,161,0.18)] sm:p-6"
    >
      <div className="mb-5 flex items-start gap-3">
        <div className="rounded-2xl border border-[#C8D7F0] bg-[#EEF5FF] p-3 text-[#0D47A1]">
          <Radar className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-[#173B7A] sm:text-2xl">More Signals We Picked Up</h2>
          <p className="mt-1 text-sm leading-6 text-[#5B6780]">
            These extra hints came from your activity and conversations. We only surface them if they look usable.
          </p>
        </div>
      </div>

      {insights.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {insights.map((group) => (
            <div key={group.label} className="rounded-[26px] border border-[#DCE4F2] bg-[#F8FBFF] p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[#7A87A3]">{group.label}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {group.items.map((item) => (
                  <span
                    key={`${group.label}-${item}`}
                    className="rounded-full border border-[#D7DFEC] bg-white px-3 py-1.5 text-sm text-[#35548D]"
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
        <details className="mt-5 rounded-[24px] border border-[#D7DFEC] bg-[#F8FBFF] p-4 text-sm text-[#5B6780]">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 font-semibold text-[#35548D]">
            Advanced raw data
            <ChevronDown className="h-4 w-4" />
          </summary>
          <pre className="mt-4 overflow-x-auto rounded-2xl border border-[#DCE4F2] bg-white p-4 text-xs leading-6 text-[#4A5976]">
            {JSON.stringify(rawPreferencesJson, null, 2) ?? ''}
          </pre>
        </details>
      )}
    </motion.section>
  );
}
