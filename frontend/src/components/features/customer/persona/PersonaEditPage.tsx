'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertTriangle, CheckCircle2, X } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { customerPersonaService } from '@/services/customer/personaService';
import { CustomerPersona, CustomerPersonaDraft, CustomerPersonaUpdatePayload } from '@/types/customer/persona';
import { PersonaEditHeader } from './PersonaEditHeader';
import { PersonaEditIdentitySection } from './PersonaEditIdentitySection';
import { PersonaEditPreferenceGroup } from './PersonaEditPreferenceGroup';
import { PersonaEditAdvancedSection } from './PersonaEditAdvancedSection';
import { PersonaEditFooter } from './PersonaEditFooter';
import { PersonaEditSkeleton } from './PersonaEditSkeleton';
import { PersonaEditEmptyState } from './PersonaEditEmptyState';
import { DeletePersonaModal } from './DeletePersonaModal';

type PreferenceFieldKey = 'food_preferences' | 'color_preferences' | 'music_preferences' | 'personality_tags';
type ValidationErrors = Partial<Record<'name' | 'birthday', string>>;

const PREFERENCE_GROUPS: Array<{
  key: PreferenceFieldKey;
  title: string;
  subtitle: string;
  icon: string;
  suggestions: string[];
}> = [
  {
    key: 'food_preferences',
    title: 'Food & Dining',
    subtitle: 'Cuisines, flavors, and dining styles you love',
    icon: '🍽️',
    suggestions: ['Italian', 'Japanese', 'Seafood', 'Vegan', 'Spicy', 'Comfort food', 'Fine dining', 'Street food', 'Brunch', 'Desserts', 'Fusion', 'Healthy'],
  },
  {
    key: 'color_preferences',
    title: 'Color Palette',
    subtitle: 'Colors that resonate with your style',
    icon: '🎨',
    suggestions: ['Emerald', 'Ivory', 'Gold', 'Navy', 'Blush', 'Terracotta', 'Lilac', 'Black', 'Silver', 'Sage', 'Champagne', 'Coral'],
  },
  {
    key: 'music_preferences',
    title: 'Music & Vibes',
    subtitle: 'Sounds that set the mood for your moments',
    icon: '🎵',
    suggestions: ['Jazz', 'R&B', 'Pop', 'Classical', 'Acoustic', 'Indie', 'Soul', 'House', 'Lo-fi', 'Afrobeats', 'Romantic', 'Throwbacks'],
  },
  {
    key: 'personality_tags',
    title: 'Personality Traits',
    subtitle: 'Words that describe your style and approach',
    icon: '✨',
    suggestions: ['Thoughtful', 'Elegant', 'Playful', 'Minimal', 'Bold', 'Romantic', 'Curious', 'Warm', 'Adventurous', 'Detail-focused', 'Social', 'Calm'],
  },
];

const normalizeChip = (value: string) => value.trim().replace(/\s+/g, ' ');
const lowerChip = (value: string) => normalizeChip(value).toLowerCase();

const uniqueChips = (values: string[]) => {
  const seen = new Set<string>();
  return values.reduce<string[]>((acc, value) => {
    const normalized = normalizeChip(value);
    if (!normalized) return acc;
    const key = normalized.toLowerCase();
    if (seen.has(key)) return acc;
    seen.add(key);
    acc.push(normalized);
    return acc;
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

const validateDraft = (draft: CustomerPersonaDraft): ValidationErrors => {
  const errors: ValidationErrors = {};
  if (!draft.name.trim()) {
    errors.name = 'Name is required';
  }
  if (draft.birthday) {
    const date = new Date(draft.birthday);
    if (Number.isNaN(date.getTime())) {
      errors.birthday = 'Invalid date format';
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
  if (!persona) return false;
  const original = draftToPayload(buildDraft(persona));
  const current = draftToPayload(draft);
  return JSON.stringify(original) !== JSON.stringify(current);
};

function PersonaEditContent() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<CustomerPersonaDraft | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const personasQuery = useQuery({
    queryKey: ['customer-personas'],
    queryFn: async () => {
      const response = await customerPersonaService.listPersonas();
      if (!response.ok) throw new Error(response.error || 'Failed to load personas');
      return response.data ?? [];
    },
    staleTime: 30_000,
  });

  const selectedPersonaId = useMemo(() => {
    const personas = personasQuery.data ?? [];
    if (!personas.length) return null;
    return personas[0].persona_id;
  }, [personasQuery.data]);

  const personaQuery = useQuery({
    queryKey: ['customer-persona', selectedPersonaId],
    enabled: Boolean(selectedPersonaId),
    queryFn: async () => {
      const response = await customerPersonaService.getPersona(selectedPersonaId as string);
      if (!response.ok || !response.data) throw new Error(response.error || 'Failed to load persona');
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
    if (!successMessage) return;
    const timer = setTimeout(() => setSuccessMessage(null), 3000);
    return () => clearTimeout(timer);
  }, [successMessage]);

  const updateMutation = useMutation({
    mutationFn: async (payload: CustomerPersonaUpdatePayload) => {
      if (!selectedPersonaId) throw new Error('Persona not found');
      const response = await customerPersonaService.updatePersona(selectedPersonaId, payload);
      if (!response.ok || !response.data) throw new Error(response.error || 'Failed to save changes');
      return response.data;
    },
    onSuccess: (updated: CustomerPersona) => {
      queryClient.setQueryData(['customer-persona', updated.persona_id], updated);
      queryClient.setQueryData<CustomerPersona[]>(['customer-personas'], (existing) =>
        existing?.map((p) => (p.persona_id === updated.persona_id ? updated : p)) ?? existing
      );
      setDraft(buildDraft(updated));
      setSuccessMessage('Changes saved successfully');
      setErrorMessage(null);
    },
    onError: (error: Error) => {
      setErrorMessage(error.message || 'Failed to save changes');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPersonaId) throw new Error('Persona not found');
      const response = await customerPersonaService.deletePersona(selectedPersonaId);
      if (!response.ok) throw new Error(response.error || 'Failed to delete persona');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customer-personas'] });
      router.push(ROUTES.CUSTOMER.DASHBOARD);
    },
    onError: (error: Error) => {
      setErrorMessage(error.message || 'Failed to delete persona');
      setShowDeleteModal(false);
    },
  });

  const persona = personaQuery.data;
  const isLoading = personasQuery.isLoading || (selectedPersonaId && personaQuery.isLoading);
  const isDirty = draft ? hasDraftChanged(draft, persona) : false;

  const setFieldValue = (field: keyof CustomerPersonaDraft, value: string) => {
    setDraft((current) => (current ? { ...current, [field]: value } : current));
    setSuccessMessage(null);
  };

  const toggleChip = (field: PreferenceFieldKey, value: string) => {
    const normalized = normalizeChip(value);
    if (!normalized) return;
    setDraft((current) => {
      if (!current) return current;
      const exists = current[field].some((item) => lowerChip(item) === lowerChip(normalized));
      const nextValues = exists
        ? current[field].filter((item) => lowerChip(item) !== lowerChip(normalized))
        : [...current[field], normalized];
      return { ...current, [field]: uniqueChips(nextValues) };
    });
    setSuccessMessage(null);
  };

  const addChip = (field: PreferenceFieldKey, value: string) => {
    const normalized = normalizeChip(value);
    if (!normalized) return;
    setDraft((current) => {
      if (!current) return current;
      return { ...current, [field]: uniqueChips([...current[field], normalized]) };
    });
    setSuccessMessage(null);
  };

  const handleSave = async () => {
    if (!draft) return;
    const errors = validateDraft(draft);
    setValidationErrors(errors);
    if (Object.keys(errors).length > 0) {
      setErrorMessage('Please fix validation errors');
      return;
    }
    await updateMutation.mutateAsync(draftToPayload(draft));
  };

  const handleReset = () => {
    if (persona) {
      setDraft(buildDraft(persona));
      setValidationErrors({});
      setSuccessMessage(null);
      setErrorMessage(null);
    }
  };

  const handleDelete = () => {
    deleteMutation.mutate();
  };

  if (isLoading || !draft) {
    return (
      <div className="min-h-screen bg-[#0a0d14]">
        <PersonaEditSkeleton />
      </div>
    );
  }

  if (!personasQuery.data?.length || !persona) {
    return (
      <div className="min-h-screen bg-[#0a0d14]">
        <PersonaEditEmptyState />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0d14] pb-32">
      <PersonaEditHeader />

      <div className="mx-auto max-w-3xl px-4 pt-6 sm:px-6">
        <AnimatePresence>
          {successMessage && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-4 flex items-center gap-3 rounded-2xl border border-[#5dd7c4]/20 bg-[#5dd7c4]/10 px-4 py-3 text-[#d7fff7]"
            >
              <CheckCircle2 className="h-5 w-5 shrink-0" />
              <span className="text-sm font-medium">{successMessage}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {errorMessage && (
          <div className="mb-4 flex items-center gap-3 rounded-2xl border border-[#ff9d9d]/20 bg-[#ff9d9d]/10 px-4 py-3 text-[#ffd0d0]">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <span className="text-sm font-medium">{errorMessage}</span>
            <button type="button" onClick={() => setErrorMessage(null)} className="ml-auto">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        <PersonaEditIdentitySection
          draft={draft}
          validationErrors={validationErrors}
          onFieldChange={setFieldValue}
        />

        {PREFERENCE_GROUPS.map((group) => (
          <PersonaEditPreferenceGroup
            key={group.key}
            title={group.title}
            subtitle={group.subtitle}
            icon={group.icon}
            values={draft[group.key]}
            suggestions={group.suggestions}
            onToggle={(value) => toggleChip(group.key, value)}
            onAdd={(value) => addChip(group.key, value)}
          />
        ))}

        <PersonaEditAdvancedSection preferencesJson={draft.preferences_json} />
      </div>

      <PersonaEditFooter
        isDirty={isDirty}
        isSaving={updateMutation.isPending}
        onSave={handleSave}
        onReset={handleReset}
        onDelete={() => setShowDeleteModal(true)}
      />

      <DeletePersonaModal
        isOpen={showDeleteModal}
        isDeleting={deleteMutation.isPending}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDelete}
      />
    </div>
  );
}

export default function PersonaEditPage() {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={queryClient}>
      <PersonaEditContent />
    </QueryClientProvider>
  );
}
