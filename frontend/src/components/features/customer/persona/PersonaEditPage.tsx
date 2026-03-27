'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertTriangle, CheckCircle2, X } from 'lucide-react';
import { ROUTES } from '@/lib/routes';
import { customerPersonaService } from '@/services/customer/personaService';
import {
  CustomerPersona,
  CustomerPersonaCreatePayload,
  CustomerPersonaDraft,
  CustomerPersonaUpdatePayload,
} from '@/types/customer/persona';
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

const EMPTY_DRAFT: CustomerPersonaDraft = {
  name: '',
  relationship: '',
  birthday: '',
  personality: '',
  preferences_json: null,
  food_preferences: [],
  color_preferences: [],
  music_preferences: [],
  personality_tags: [],
};

type PersonaEditPageProps = {
  mode?: 'create' | 'edit';
  personaId?: string;
};

function PersonaEditContent({ mode = 'edit', personaId }: PersonaEditPageProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const isCreateMode = mode === 'create';
  const [draft, setDraft] = useState<CustomerPersonaDraft | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hasHydrated, setHasHydrated] = useState(false);

  useEffect(() => {
    setHasHydrated(true);
  }, []);

  const personasQuery = useQuery({
    queryKey: ['customer-personas'],
    enabled: hasHydrated && !isCreateMode,
    queryFn: async () => {
      const response = await customerPersonaService.listPersonas();
      if (!response.ok) throw new Error(response.error || 'Failed to load personas');
      return response.data ?? [];
    },
    staleTime: 30_000,
  });

  const selectedPersonaId = useMemo(() => {
    if (isCreateMode) return null;
    if (personaId) return personaId;
    const personas = personasQuery.data ?? [];
    if (!personas.length) return null;
    return personas[0].persona_id;
  }, [isCreateMode, personaId, personasQuery.data]);

  const personaQuery = useQuery({
    queryKey: ['customer-persona', selectedPersonaId],
    enabled: hasHydrated && !isCreateMode && Boolean(selectedPersonaId),
    queryFn: async () => {
      const response = await customerPersonaService.getPersona(selectedPersonaId as string);
      if (!response.ok || !response.data) throw new Error(response.error || 'Failed to load persona');
      return response.data;
    },
    staleTime: 30_000,
  });

  useEffect(() => {
    const error = personasQuery.error;
    if (!error) return;
    const message = error instanceof Error ? error.message : 'Unable to load personas';
    setErrorMessage(message);
  }, [personasQuery.error]);

  useEffect(() => {
    const error = personaQuery.error;
    if (!error) return;
    const message = error instanceof Error ? error.message : 'Unable to load persona';
    setErrorMessage(message);
  }, [personaQuery.error]);

  useEffect(() => {
    if (isCreateMode) {
      setDraft(EMPTY_DRAFT);
      setValidationErrors({});
      setErrorMessage(null);
      return;
    }

    if (personaQuery.data) {
      setDraft(buildDraft(personaQuery.data));
      setValidationErrors({});
      setErrorMessage(null);
    }
  }, [isCreateMode, personaQuery.data]);

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

  const createMutation = useMutation({
    mutationFn: async (payload: CustomerPersonaCreatePayload) => {
      const response = await customerPersonaService.createPersona(payload);
      if (!response.ok || !response.data) throw new Error(response.error || 'Failed to create persona');
      return response.data;
    },
    onSuccess: (created: CustomerPersona) => {
      queryClient.setQueryData<CustomerPersona[]>(['customer-personas'], (existing) => [
        created,
        ...(existing ?? []),
      ]);
      queryClient.setQueryData(['customer-persona', created.persona_id], created);
      setDraft(buildDraft(created));
      setSuccessMessage('Persona created successfully');
      setErrorMessage(null);
      router.push(ROUTES.CUSTOMER.PERSONA);
    },
    onError: (error: Error) => {
      setErrorMessage(error.message || 'Failed to create persona');
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
      router.push(ROUTES.CUSTOMER.PERSONA);
    },
    onError: (error: Error) => {
      setErrorMessage(error.message || 'Failed to delete persona');
      setShowDeleteModal(false);
    },
  });

  const persona = personaQuery.data;
  const isLoading = isCreateMode
    ? draft === null
    : personasQuery.isLoading || (selectedPersonaId && personaQuery.isLoading);
  const isDirty = draft
    ? (isCreateMode
      ? JSON.stringify(draftToPayload(draft)) !== JSON.stringify(draftToPayload(EMPTY_DRAFT))
      : hasDraftChanged(draft, persona))
    : false;

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
    if (isCreateMode) {
      await createMutation.mutateAsync(draftToPayload(draft) as CustomerPersonaCreatePayload);
      return;
    }

    await updateMutation.mutateAsync(draftToPayload(draft));
  };

  const handleReset = () => {
    if (isCreateMode) {
      setDraft(EMPTY_DRAFT);
      setValidationErrors({});
      setSuccessMessage(null);
      setErrorMessage(null);
      return;
    }

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
      <div className="min-h-screen bg-[#F4F8FA]">
        <PersonaEditSkeleton />
      </div>
    );
  }

  if (!isCreateMode && (!personasQuery.data?.length || !persona)) {
    return (
      <div className="min-h-screen bg-[#F4F8FA]">
        <PersonaEditEmptyState />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F4F8FA] pb-32">
      <PersonaEditHeader mode={mode} />

      <div className="mx-auto max-w-3xl px-4 pt-6 sm:px-6">
        <AnimatePresence>
          {successMessage && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-4 flex items-center gap-3 rounded-2xl border border-[#B7E4C7] bg-[#F0FBF4] px-4 py-3 text-[#1F7D46]"
            >
              <CheckCircle2 className="h-5 w-5 shrink-0" />
              <span className="text-sm font-medium">{successMessage}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {errorMessage && (
          <div className="mb-4 flex items-center gap-3 rounded-2xl border border-[#F4CDCD] bg-[#FFF4F4] px-4 py-3 text-[#B23C3C]">
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
        isSaving={updateMutation.isPending || createMutation.isPending}
        onSave={handleSave}
        onReset={handleReset}
        onDelete={isCreateMode ? undefined : () => setShowDeleteModal(true)}
        saveLabel={isCreateMode ? 'Create Persona' : 'Save Changes'}
      />

      {!isCreateMode && (
        <DeletePersonaModal
          isOpen={showDeleteModal}
          isDeleting={deleteMutation.isPending}
          onClose={() => setShowDeleteModal(false)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}

export default function PersonaEditPage({ mode = 'edit', personaId }: PersonaEditPageProps) {
  const [queryClient] = useState(() => new QueryClient());
  return (
    <QueryClientProvider client={queryClient}>
      <PersonaEditContent mode={mode} personaId={personaId} />
    </QueryClientProvider>
  );
}
