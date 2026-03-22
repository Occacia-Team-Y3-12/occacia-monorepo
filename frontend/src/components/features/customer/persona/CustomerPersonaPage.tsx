'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  keepPreviousData,
  QueryClient,
  QueryClientProvider,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, RefreshCw, Undo2 } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { customerPersonaService } from '@/services/customer/personaService';
import {
  CustomerPersona,
  CustomerPersonaDraft,
  CustomerPersonaUpdatePayload,
} from '@/types/customer/persona';
import { PersonaConfirmationBar } from './PersonaConfirmationBar';
import { PersonaEmptyState } from './PersonaEmptyState';
import { PersonaInsightsSection } from './PersonaInsightsSection';
import { PersonaPreferenceGroup } from './PersonaPreferenceGroup';
import { PersonaReviewHero } from './PersonaReviewHero';
import { PersonaReviewSkeleton } from './PersonaReviewSkeleton';
import { PersonaSummaryCard } from './PersonaSummaryCard';

type PreferenceFieldKey =
  | 'food_preferences'
  | 'color_preferences'
  | 'music_preferences'
  | 'personality_tags';

type ValidationErrors = Partial<Record<'name' | 'birthday', string>>;

type InsightGroup = {
  label: string;
  items: string[];
};

type PreferenceUiState = Record<PreferenceFieldKey, { search: string; draft: string; expanded: boolean }>;

const PREFERENCE_GROUPS: Array<{
  key: PreferenceFieldKey;
  title: string;
  caption: string;
  accentClassName: string;
  suggestions: string[];
}> = [
  {
    key: 'food_preferences',
    title: 'Food Preferences',
    caption: 'Flavors, cuisines, and dining moods we think you naturally lean toward.',
    accentClassName: 'from-[#f97316]/30 via-[#f5c871]/15 to-transparent',
    suggestions: ['Italian', 'Japanese', 'Seafood', 'Comfort food', 'Brunch', 'Desserts', 'Spicy', 'Vegan', 'Fusion', 'Fine dining', 'Street food', 'Healthy bowls'],
  },
  {
    key: 'color_preferences',
    title: 'Color Preferences',
    caption: 'Palette cues that can shape decor, invitations, florals, and styling.',
    accentClassName: 'from-[#5dd7c4]/25 via-[#60a5fa]/15 to-transparent',
    suggestions: ['Emerald', 'Ivory', 'Gold', 'Navy', 'Blush', 'Terracotta', 'Lilac', 'Black', 'Silver', 'Sage', 'Champagne', 'Coral'],
  },
  {
    key: 'music_preferences',
    title: 'Music Preferences',
    caption: 'Sound and vibe selections for moments, dinners, and celebrations.',
    accentClassName: 'from-[#a78bfa]/25 via-[#f472b6]/15 to-transparent',
    suggestions: ['Jazz', 'R&B', 'Pop', 'Classical', 'Acoustic', 'Afrobeats', 'Indie', 'Lo-fi', 'Soul', 'House', 'Romantic', 'Throwbacks'],
  },
  {
    key: 'personality_tags',
    title: 'Personality Tags',
    caption: 'Traits we picked up that help tailor recommendation tone and event style.',
    accentClassName: 'from-[#f5c871]/25 via-[#fb7185]/15 to-transparent',
    suggestions: ['Thoughtful', 'Elegant', 'Playful', 'Minimal', 'Bold', 'Romantic', 'Curious', 'Warm', 'Adventurous', 'Detail-focused', 'Social', 'Calm'],
  },
];

const normalizeChip = (value: string) => value.trim().replace(/\s+/g, ' ');
const lowerChip = (value: string) => normalizeChip(value).toLowerCase();

const uniqueChips = (values: string[]) => {
  const seen = new Set<string>();

  return values.reduce<string[]>((accumulator, value) => {
    const normalized = normalizeChip(value);
    if (!normalized) {
      return accumulator;
    }

    const key = normalized.toLowerCase();
    if (seen.has(key)) {
      return accumulator;
    }

    seen.add(key);
    accumulator.push(normalized);
    return accumulator;
  }, []);
};

const buildDraft = (persona: CustomerPersona): CustomerPersonaDraft => ({
  name: persona.name ?? '',
  relationship: persona.relationship ?? '',
  birthday: persona.birthday ? persona.birthday.slice(0, 10) : '',
  personality: persona.personality ?? '',
  preferences_json: persona.preferences_json ?? null,
  food_preferences: uniqueChips(persona.food_preferences ?? []),
  color_preferences: uniqueChips(persona.color_preferences ?? []),
  music_preferences: uniqueChips(persona.music_preferences ?? []),
  personality_tags: uniqueChips(persona.personality_tags ?? []),
});

const formatDateLabel = (value: string | null, prefix: string) => {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return `${prefix} ${new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)}`;
};

const validateDraft = (draft: CustomerPersonaDraft): ValidationErrors => {
  const errors: ValidationErrors = {};

  if (!draft.name.trim()) {
    errors.name = 'Please add a name before saving or confirming.';
  }

  if (draft.birthday) {
    const date = new Date(draft.birthday);
    if (Number.isNaN(date.getTime())) {
      errors.birthday = 'Birthday needs to be a valid date.';
    }
  }

  return errors;
};

const draftToPayload = (draft: CustomerPersonaDraft): CustomerPersonaUpdatePayload => ({
  name: draft.name.trim(),
  relationship: draft.relationship.trim() || null,
  birthday: draft.birthday || null,
  personality: draft.personality.trim() || null,
  preferences_json: draft.preferences_json ?? null,
  food_preferences: uniqueChips(draft.food_preferences),
  color_preferences: uniqueChips(draft.color_preferences),
  music_preferences: uniqueChips(draft.music_preferences),
  personality_tags: uniqueChips(draft.personality_tags),
});

const hasDraftChanged = (draft: CustomerPersonaDraft, persona: CustomerPersona | undefined) => {
  if (!persona) {
    return false;
  }

  const original = draftToPayload(buildDraft(persona));
  const current = draftToPayload(draft);
  return JSON.stringify(original) !== JSON.stringify(current);
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const flattenInsightValue = (value: unknown): string[] => {
  if (typeof value === 'string') {
    const trimmed = normalizeChip(value);
    return trimmed ? [trimmed] : [];
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return [String(value)];
  }

  if (Array.isArray(value)) {
    return uniqueChips(value.flatMap(flattenInsightValue));
  }

  if (isRecord(value)) {
    return uniqueChips(Object.entries(value).flatMap(([key, nested]) => {
      if (typeof nested === 'boolean') {
        return nested ? [key] : [];
      }

      return flattenInsightValue(nested);
    }));
  }

  return [];
};

const buildInsightGroups = (raw: unknown): InsightGroup[] => {
  if (!isRecord(raw)) {
    return [];
  }

  return Object.entries(raw)
    .map(([key, value]) => ({
      label: key.replace(/_/g, ' '),
      items: flattenInsightValue(value).slice(0, 8),
    }))
    .filter((group) => group.items.length > 0)
    .slice(0, 6);
};

function CustomerPersonaContent() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<CustomerPersonaDraft | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [isEditingDetails, setIsEditingDetails] = useState(false);
  const [successVisible, setSuccessVisible] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [preferenceUi, setPreferenceUi] = useState<PreferenceUiState>({
    food_preferences: { search: '', draft: '', expanded: false },
    color_preferences: { search: '', draft: '', expanded: false },
    music_preferences: { search: '', draft: '', expanded: false },
    personality_tags: { search: '', draft: '', expanded: false },
  });

  const personasQuery = useQuery({
    queryKey: ['customer-personas'],
    queryFn: async () => {
      const response = await customerPersonaService.listPersonas();
      if (!response.ok) {
        throw new Error(response.error || 'Failed to load personas.');
      }

      return response.data ?? [];
    },
    staleTime: 30_000,
    placeholderData: keepPreviousData,
  });

  const selectedPersonaId = useMemo(() => {
    const personas = personasQuery.data ?? [];
    if (!personas.length) {
      return null;
    }

    const firstUnconfirmed = personas.find((persona: CustomerPersona) => !persona.is_confirmed);
    return (firstUnconfirmed ?? personas[0]).persona_id;
  }, [personasQuery.data]);

  const personaQuery = useQuery({
    queryKey: ['customer-persona', selectedPersonaId],
    enabled: Boolean(selectedPersonaId),
    queryFn: async () => {
      const response = await customerPersonaService.getPersona(selectedPersonaId as string);
      if (!response.ok || !response.data) {
        throw new Error(response.error || 'Failed to load persona details.');
      }

      return response.data;
    },
    staleTime: 30_000,
  });

  useEffect(() => {
    if (personaQuery.data) {
      setDraft(buildDraft(personaQuery.data));
      setValidationErrors({});
      setErrorMessage(null);
    }
  }, [personaQuery.data]);

  useEffect(() => {
    if (!successVisible) {
      return undefined;
    }

    const timer = window.setTimeout(() => setSuccessVisible(false), 2800);
    return () => window.clearTimeout(timer);
  }, [successVisible]);

  const updateMutation = useMutation({
    mutationFn: async (payload: CustomerPersonaUpdatePayload) => {
      if (!selectedPersonaId) {
        throw new Error('Persona not found.');
      }

      const response = await customerPersonaService.updatePersona(selectedPersonaId, payload);
      if (!response.ok || !response.data) {
        throw new Error(response.error || 'Unable to save persona changes.');
      }

      return response.data;
    },
    onSuccess: (updatedPersona: CustomerPersona) => {
      queryClient.setQueryData(['customer-persona', updatedPersona.persona_id], updatedPersona);
      queryClient.setQueryData<CustomerPersona[] | undefined>(['customer-personas'], (existing: CustomerPersona[] | undefined) => (
        existing?.map((persona: CustomerPersona) => (
          persona.persona_id === updatedPersona.persona_id ? updatedPersona : persona
        )) ?? existing
      ));
      setDraft(buildDraft(updatedPersona));
      setFeedbackMessage('Persona details saved.');
      setErrorMessage(null);
    },
    onError: (error: Error) => {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to save persona changes.');
    },
  });

  const confirmMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPersonaId) {
        throw new Error('Persona not found.');
      }

      const response = await customerPersonaService.confirmPersona(selectedPersonaId);
      if (!response.ok) {
        throw new Error(response.error || 'Unable to confirm persona.');
      }

      return response.data;
    },
    onSuccess: (confirmedPersona: CustomerPersona | null) => {
      if (confirmedPersona) {
        queryClient.setQueryData(['customer-persona', confirmedPersona.persona_id], confirmedPersona);
        queryClient.setQueryData<CustomerPersona[] | undefined>(['customer-personas'], (existing: CustomerPersona[] | undefined) => (
          existing?.map((persona: CustomerPersona) => (
            persona.persona_id === confirmedPersona.persona_id ? confirmedPersona : persona
          )) ?? existing
        ));
        setDraft(buildDraft(confirmedPersona));
      } else {
        queryClient.invalidateQueries({ queryKey: ['customer-personas'] });
        queryClient.invalidateQueries({ queryKey: ['customer-persona', selectedPersonaId] });
      }

      setFeedbackMessage('Persona confirmed. Future recommendations will feel sharper.');
      setErrorMessage(null);
      setSuccessVisible(true);
    },
    onError: (error: Error) => {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to confirm persona.');
    },
  });

  const unconfirmMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPersonaId) {
        throw new Error('Persona not found.');
      }

      const response = await customerPersonaService.unconfirmPersona(selectedPersonaId);
      if (!response.ok) {
        throw new Error(response.error || 'Unable to remove confirmation.');
      }

      return response.data;
    },
    onSuccess: (updatedPersona: CustomerPersona | null) => {
      if (updatedPersona) {
        queryClient.setQueryData(['customer-persona', updatedPersona.persona_id], updatedPersona);
        queryClient.setQueryData<CustomerPersona[] | undefined>(['customer-personas'], (existing: CustomerPersona[] | undefined) => (
          existing?.map((persona: CustomerPersona) => (
            persona.persona_id === updatedPersona.persona_id ? updatedPersona : persona
          )) ?? existing
        ));
        setDraft(buildDraft(updatedPersona));
      } else {
        queryClient.invalidateQueries({ queryKey: ['customer-personas'] });
        queryClient.invalidateQueries({ queryKey: ['customer-persona', selectedPersonaId] });
      }

      setFeedbackMessage('Confirmation removed. You can revisit this any time.');
      setErrorMessage(null);
    },
    onError: (error: Error) => {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to remove confirmation.');
    },
  });

  const persona = personaQuery.data;
  const isLoading = personasQuery.isLoading || (selectedPersonaId !== null && personaQuery.isLoading);
  const isDirty = draft ? hasDraftChanged(draft, persona) : false;
  const insightGroups = useMemo(() => buildInsightGroups(draft?.preferences_json ?? null), [draft?.preferences_json]);
  const lastUpdatedLabel = persona ? formatDateLabel(persona.updated_at, 'Updated') : null;
  const confirmedLabel = persona?.is_confirmed ? formatDateLabel(persona.confirmed_at, 'Confirmed') : null;

  const setFieldValue = (field: keyof CustomerPersonaDraft, value: string) => {
    setDraft((current) => (current ? { ...current, [field]: value } : current));
    setFeedbackMessage(null);
  };

  const updatePreferenceUi = (field: PreferenceFieldKey, patch: Partial<PreferenceUiState[PreferenceFieldKey]>) => {
    setPreferenceUi((current) => ({
      ...current,
      [field]: { ...current[field], ...patch },
    }));
  };

  const toggleChip = (field: PreferenceFieldKey, value: string) => {
    const normalizedValue = normalizeChip(value);
    if (!normalizedValue) {
      return;
    }

    setDraft((current) => {
      if (!current) {
        return current;
      }

      const exists = current[field].some((item) => lowerChip(item) === lowerChip(normalizedValue));
      const nextValues = exists
        ? current[field].filter((item) => lowerChip(item) !== lowerChip(normalizedValue))
        : [...current[field], normalizedValue];

      return {
        ...current,
        [field]: uniqueChips(nextValues),
      };
    });
  };

  const addChip = (field: PreferenceFieldKey, value: string) => {
    const normalizedValue = normalizeChip(value);
    if (!normalizedValue) {
      return;
    }

    setDraft((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        [field]: uniqueChips([...current[field], normalizedValue]),
      };
    });
    updatePreferenceUi(field, { draft: '', search: normalizedValue });
  };

  const saveDraft = async () => {
    if (!draft) {
      return null;
    }

    const errors = validateDraft(draft);
    setValidationErrors(errors);

    if (Object.keys(errors).length > 0) {
      setErrorMessage('Please fix the highlighted details before continuing.');
      return null;
    }

    if (!isDirty && persona) {
      return persona;
    }

    return updateMutation.mutateAsync(draftToPayload(draft));
  };

  const handleConfirm = async () => {
    try {
      const saved = await saveDraft();
      if (!saved && !persona) {
        return;
      }

      await confirmMutation.mutateAsync();
    } catch {
      // handled by mutation callbacks
    }
  };

  const handleSkip = () => {
    router.push(ROUTES.CUSTOMER.DASHBOARD);
  };

  if (isLoading || !draft) {
    return (
      <div className="min-h-[calc(100vh-160px)] rounded-[40px] bg-[#080b14] p-4 sm:p-6 lg:p-8">
        <PersonaReviewSkeleton />
      </div>
    );
  }

  if (personasQuery.isError || personaQuery.isError) {
    return (
      <div className="flex min-h-[65vh] flex-col items-center justify-center rounded-[36px] border border-white/10 bg-[#0b0f1a] px-6 py-12 text-center">
        <div className="rounded-[28px] border border-[#ff9d9d]/20 bg-[#ff9d9d]/10 p-4 text-[#ffbebe]">
          <RefreshCw className="h-8 w-8" />
        </div>
        <h1 className="mt-5 text-3xl font-semibold text-white">We couldn&apos;t load your persona just now</h1>
        <p className="mt-3 max-w-lg text-white/60">
          {(personasQuery.error instanceof Error && personasQuery.error.message)
            || (personaQuery.error instanceof Error && personaQuery.error.message)
            || 'Please try again in a moment.'}
        </p>
        <button
          type="button"
          onClick={() => {
            personasQuery.refetch();
            personaQuery.refetch();
          }}
          className="mt-6 rounded-full bg-[#f5c871] px-5 py-3 text-sm font-semibold text-[#171a23]"
        >
          Try again
        </button>
      </div>
    );
  }

  if (!personasQuery.data?.length || !persona) {
    return (
      <div className="min-h-[calc(100vh-160px)] rounded-[40px] bg-[#080b14] p-4 sm:p-6 lg:p-8">
        <PersonaEmptyState />
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-160px)] rounded-[40px] bg-[radial-gradient(circle_at_top,_rgba(245,200,113,0.08),_transparent_20%),linear-gradient(180deg,#080b14_0%,#070911_100%)] p-4 sm:p-6 lg:p-8">
      <div className="mx-auto max-w-5xl space-y-5">
        <PersonaReviewHero isConfirmed={persona.is_confirmed} />

        <AnimatePresence>
          {successVisible && (
            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -12 }}
              className="rounded-[28px] border border-[#5dd7c4]/20 bg-[#5dd7c4]/10 p-4 text-[#d7fff7] shadow-[0_18px_45px_rgba(18,88,74,0.28)]"
            >
              <div className="flex items-start gap-3">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" />
                <div>
                  <p className="font-semibold">Persona confirmed</p>
                  <p className="mt-1 text-sm text-[#d7fff7]/80">
                    We&apos;ll use this profile to tune future recommendations and event ideas.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {(feedbackMessage || errorMessage) && (
          <div
            className={`rounded-[24px] border px-4 py-3 text-sm ${
              errorMessage
                ? 'border-[#ff9d9d]/20 bg-[#ff9d9d]/10 text-[#ffd0d0]'
                : 'border-[#f5c871]/20 bg-[#f5c871]/10 text-[#ffe2a2]'
            }`}
          >
            {errorMessage || feedbackMessage}
          </div>
        )}

        <PersonaSummaryCard
          draft={draft}
          isConfirmed={persona.is_confirmed}
          lastUpdatedLabel={lastUpdatedLabel}
          confirmedLabel={confirmedLabel}
          isEditing={isEditingDetails}
          validationErrors={validationErrors}
          onStartEditing={() => setIsEditingDetails(true)}
          onCancelEditing={() => setIsEditingDetails(false)}
          onFieldChange={setFieldValue}
        />

        {PREFERENCE_GROUPS.map((group) => (
          <PersonaPreferenceGroup
            key={group.key}
            title={group.title}
            caption={group.caption}
            values={draft[group.key]}
            suggestions={group.suggestions}
            searchValue={preferenceUi[group.key].search}
            draftValue={preferenceUi[group.key].draft}
            onSearchChange={(value) => updatePreferenceUi(group.key, { search: value })}
            onDraftValueChange={(value) => updatePreferenceUi(group.key, { draft: value })}
            onToggle={(value) => toggleChip(group.key, value)}
            onAdd={(value) => addChip(group.key, value)}
            expanded={preferenceUi[group.key].expanded}
            onToggleExpanded={() => updatePreferenceUi(group.key, {
              expanded: !preferenceUi[group.key].expanded,
            })}
            accentClassName={group.accentClassName}
          />
        ))}

        <PersonaInsightsSection
          insights={insightGroups}
          rawPreferencesJson={draft.preferences_json}
        />

        <div className="flex flex-wrap items-center gap-3 rounded-[28px] border border-white/10 bg-white/[0.03] px-4 py-4 text-sm text-white/60">
          <button
            type="button"
            onClick={() => setIsEditingDetails(true)}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white/78 transition hover:bg-white/10"
          >
            Edit details
          </button>
          {persona.is_confirmed && (
            <button
              type="button"
              onClick={() => unconfirmMutation.mutate()}
              disabled={unconfirmMutation.isPending}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-transparent px-4 py-2 text-sm font-semibold text-white/72 transition hover:bg-white/6 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Undo2 className="h-4 w-4" />
              {unconfirmMutation.isPending ? 'Updating...' : 'Remove confirmation'}
            </button>
          )}
          <span className="text-white/40">Recommendations still work even if you skip this step.</span>
        </div>

        <PersonaConfirmationBar
          isConfirmed={persona.is_confirmed}
          isDirty={isDirty}
          isSaving={updateMutation.isPending}
          isConfirming={confirmMutation.isPending}
          onConfirm={handleConfirm}
          onSkip={handleSkip}
          onEdit={() => setIsEditingDetails(true)}
        />
      </div>
    </div>
  );
}

export default function CustomerPersonaPage() {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <CustomerPersonaContent />
    </QueryClientProvider>
  );
}
