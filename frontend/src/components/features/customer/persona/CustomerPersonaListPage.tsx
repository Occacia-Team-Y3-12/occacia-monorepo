'use client';

import Link from 'next/link';
import { useState } from 'react';
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
} from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle2, Plus, Sparkles, Users } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { customerPersonaService } from '@/services/customer/personaService';

const formatDate = (value: string | null) => {
  if (!value) {
    return 'Recently updated';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return 'Recently updated';
  }

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(parsed);
};

function PersonaListContent() {
  const personasQuery = useQuery({
    queryKey: ['customer-personas'],
    queryFn: async () => {
      const response = await customerPersonaService.listPersonas();
      if (!response.ok) {
        throw new Error(response.error || 'Failed to load personas');
      }

      return response.data ?? [];
    },
    staleTime: 30_000,
  });

  if (personasQuery.isLoading) {
    return (
      <div className="min-h-[calc(100vh-160px)] rounded-[32px] bg-[#F4F8FA] p-6 sm:p-8">
        <div className="mx-auto max-w-6xl space-y-4">
          <div className="h-12 w-64 animate-pulse rounded-2xl bg-white" />
          <div className="grid gap-4 lg:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <div
                key={index}
                className="h-48 animate-pulse rounded-[28px] border border-[#DCE4F2] bg-white"
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (personasQuery.isError) {
    return (
      <div className="flex min-h-[65vh] items-center justify-center rounded-[32px] bg-[#F4F8FA] p-6">
        <div className="max-w-lg rounded-[28px] border border-[#F4CDCD] bg-white p-8 text-center shadow-[0_24px_60px_-36px_rgba(13,71,161,0.18)]">
          <h1 className="text-2xl font-semibold text-[#173B7A]">We couldn&apos;t load your people</h1>
          <p className="mt-3 text-sm leading-6 text-[#5B6780]">
            {personasQuery.error instanceof Error
              ? personasQuery.error.message
              : 'Please refresh and try again.'}
          </p>
        </div>
      </div>
    );
  }

  const personas = personasQuery.data ?? [];

  return (
    <div className="min-h-[calc(100vh-160px)] rounded-[32px] bg-[#F4F8FA] p-4 sm:p-6 lg:p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="overflow-hidden rounded-[32px] border border-[#DCE4F2] bg-[linear-gradient(140deg,#FFFFFF_0%,#F6FAFF_52%,#EEF5FF_100%)] px-6 py-8 shadow-[0_24px_60px_-36px_rgba(13,71,161,0.2)] sm:px-8"
        >
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-3">
              <div className="inline-flex items-center gap-2 rounded-full bg-[#EAF2FF] px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#0D47A1]">
                <Users className="h-3.5 w-3.5" />
                People
              </div>
              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-[#173B7A] sm:text-4xl">
                  Manage your personas
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-7 text-[#5B6780] sm:text-base">
                  Keep recipient profiles in one place so recommendations and event planning stay tailored to the right person.
                </p>
              </div>
            </div>

            <Link
              href={ROUTES.CUSTOMER.PERSONA_NEW}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-[#0D47A1] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#1C5BC3]"
            >
              <Plus className="h-4 w-4" />
              Create New Persona
            </Link>
          </div>
        </motion.section>

        {!personas.length ? (
          <motion.section
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-[32px] border border-[#DCE4F2] bg-white p-8 text-center shadow-[0_24px_60px_-36px_rgba(13,71,161,0.16)]"
          >
            <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[#EAF2FF] text-[#0D47A1]">
              <Sparkles className="h-9 w-9" />
            </div>
            <h2 className="mt-5 text-2xl font-semibold text-[#173B7A]">No personas yet</h2>
            <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-[#5B6780]">
              Add your first persona to save preferences, relationships, and profile details for future recommendations.
            </p>
            <Link
              href={ROUTES.CUSTOMER.PERSONA_NEW}
              className="mt-6 inline-flex items-center justify-center gap-2 rounded-full bg-[#0D47A1] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#1C5BC3]"
            >
              <Plus className="h-4 w-4" />
              Create Persona
            </Link>
          </motion.section>
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {personas.map((persona) => (
              <motion.article
                key={persona.persona_id}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-[28px] border border-[#DCE4F2] bg-white p-6 shadow-[0_24px_60px_-36px_rgba(13,71,161,0.16)]"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-xl font-semibold text-[#173B7A]">{persona.name}</h2>
                      {persona.is_confirmed && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-[#F0FBF4] px-2.5 py-1 text-xs font-semibold text-[#1F7D46]">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Confirmed
                        </span>
                      )}
                    </div>
                    <p className="mt-2 text-sm text-[#5B6780]">
                      {persona.relationship || 'Relationship not added'}
                    </p>
                  </div>

                  <Link
                    href={ROUTES.CUSTOMER.PERSONA_DETAIL(persona.persona_id)}
                    className="inline-flex items-center gap-2 rounded-full border border-[#D7DFEC] bg-[#F8FBFF] px-4 py-2 text-sm font-semibold text-[#0D47A1] transition hover:border-[#BFD0EE] hover:bg-[#EEF5FF]"
                  >
                    Edit
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>

                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[22px] bg-[#F8FBFF] px-4 py-3">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#7A87A3]">Birthday</p>
                    <p className="mt-2 text-sm text-[#173B7A]">{persona.birthday || 'Not added yet'}</p>
                  </div>
                  <div className="rounded-[22px] bg-[#F8FBFF] px-4 py-3">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#7A87A3]">Updated</p>
                    <p className="mt-2 text-sm text-[#173B7A]">{formatDate(persona.updated_at)}</p>
                  </div>
                </div>

                <div className="mt-5 flex flex-wrap gap-2">
                  {[...(persona.personality_tags ?? []), ...(persona.food_preferences ?? [])]
                    .slice(0, 5)
                    .map((chip) => (
                      <span
                        key={`${persona.persona_id}-${chip}`}
                        className="rounded-full bg-[#EEF5FF] px-3 py-1.5 text-xs font-medium text-[#35548D]"
                      >
                        {chip}
                      </span>
                    ))}
                </div>
              </motion.article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function CustomerPersonaListPage() {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <PersonaListContent />
    </QueryClientProvider>
  );
}
