'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { customerEventService } from '@/services/customer/eventServices';
import { ROUTES } from '@/lib/routes';
import { CreateCustomerEventPayload, CustomerPersonaOption, CustomerEventType, EventTypeOption } from '@/types/customer';

type CustomerEventFormType = CustomerEventType | string;

const DEFAULT_EVENT_TYPE: CustomerEventFormType = '';

const EVENT_TYPE_FALLBACKS: EventTypeOption[] = [
  {
    id: 'individual',
    value: 'individual',
    label: 'Individual',
    example: 'Visit someone',
    titlePlaceholder: 'e.g., Visiting to see sick mom',
  },
  {
    id: 'group',
    value: 'group',
    label: 'Group',
    example: 'Celebration',
    titlePlaceholder: 'e.g., Family dinner planning',
  },
  {
    id: 'others',
    value: 'others',
    label: 'Others',
    example: 'Appointment',
    titlePlaceholder: 'e.g., Doctor appointment this Saturday',
  },
];

export const PERSONA_OPTIONS: CustomerPersonaOption[] = [
  { id: 'john-cena', name: 'John Cena', role: 'Professional Athlete', imageUrl: '/images/customer/events/Jhon.svg' },
  { id: 'sarah-jenkins', name: 'Sarah Jenkins', role: 'Corporate Client', imageUrl: '/images/customer/events/Sarah.svg' },
  { id: 'michael-chen', name: 'Michael Chen', role: 'Vendor Manager', imageUrl: '/images/customer/events/Micheal.svg' },
];

export const useCreateEvent = () => {
  const router = useRouter();
  const [eventType, setEventType] = useState<CustomerEventFormType>(DEFAULT_EVENT_TYPE);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [eventTypes, setEventTypes] = useState<EventTypeOption[]>(EVENT_TYPE_FALLBACKS);
  const [personas, setPersonas] = useState<CustomerPersonaOption[]>(PERSONA_OPTIONS);
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>([]);
  const [errors, setErrors] = useState<{ eventType?: string; title?: string; form?: string }>({});
  const [isLoadingEventTypes, setIsLoadingEventTypes] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [draftEventId, setDraftEventId] = useState<string | null>(null);

  const selectedEventType = useMemo(
    () => eventTypes.find((type) => type.value === eventType),
    [eventType, eventTypes]
  );

  const titlePlaceholder = useMemo(
    () => selectedEventType?.titlePlaceholder || 'e.g., Visiting to see sick mom',
    [selectedEventType]
  );

  useEffect(() => {
    const loadEventTypes = async () => {
      setIsLoadingEventTypes(true);
      const result = await customerEventService.getEventTypes();

      if (result.ok && result.data?.data?.eventTypes?.length) {
        setEventTypes(result.data.data.eventTypes);
      } else if (!result.ok) {
        setErrors((prev) => ({ ...prev, form: result.error || 'Unable to load event types right now.' }));
      }

      setIsLoadingEventTypes(false);
    };

    void loadEventTypes();
  }, []);

  const togglePersona = (personaId: string) => {
    setSelectedPersonaIds((prev) =>
      prev.includes(personaId) ? prev.filter((id) => id !== personaId) : [...prev, personaId]
    );
  };

  // Adds a new local persona and pre-selects it for the event.
  const addNewPersona = (name: string, role: string) => {
    const trimmedName = name.trim();
    const trimmedRole = role.trim();

    if (!trimmedName || !trimmedRole) {
      setErrors((prev) => ({ ...prev, form: 'New person requires both name and role.' }));
      return;
    }

    const personaId = `persona_${Date.now()}`;
    const newPersona: CustomerPersonaOption = {
      id: personaId,
      name: trimmedName,
      role: trimmedRole,
    };

    setPersonas((prev) => [...prev, newPersona]);
    setSelectedPersonaIds((prev) => [...prev, personaId]);
    setErrors((prev) => ({ ...prev, form: undefined }));
  };

  const validate = () => {
    const nextErrors: { eventType?: string; title?: string } = {};

    if (!eventType) {
      nextErrors.eventType = 'Please select an event type.';
    }

    if (!title.trim()) {
      nextErrors.title = 'Event title is required.';
    } else if (title.trim().length < 3) {
      nextErrors.title = 'Event title must be at least 3 characters.';
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  // Creates draft, optionally updates personas, then redirects to event chat.
  const handleCreate = async () => {
    if (!validate()) {
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      const payload: CreateCustomerEventPayload = {
        eventType,
        title: title.trim(),
        description: description.trim() || undefined,
      };

      const createResult = await customerEventService.createEvent(payload);

      if (!createResult.ok || !createResult.data?.data?.eventId) {
        setErrors({ form: createResult.error || createResult.data?.message || 'Unable to create event. Please try again.' });
        return;
      }

      const eventId = createResult.data.data.eventId;
      setDraftEventId(eventId);
      if (typeof window !== 'undefined') {
        window.sessionStorage.setItem('customer:lastEventTitle', title.trim());
      }

      if (selectedPersonaIds.length > 0) {
        void customerEventService.updatePersonas(eventId, { personaIds: selectedPersonaIds });
      }

      router.push(ROUTES.CUSTOMER.EVENT_CHAT(eventId));
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Something went wrong while creating the event.';
      setErrors({ form: message });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Cancels event creation; if draft exists, removes it before redirecting.
  const handleCancel = async () => {
    setIsCancelling(true);

    try {
      if (draftEventId) {
        const deleteResult = await customerEventService.deleteDraft(draftEventId);

        if (!deleteResult.ok) {
          setErrors({ form: deleteResult.error || 'Unable to discard draft event right now.' });
          return;
        }
      }

      router.push(ROUTES.CUSTOMER.DASHBOARD);
    } catch {
      setErrors({ form: 'Something went wrong while cancelling the event.' });
    } finally {
      setIsCancelling(false);
    }
  };

  return {
    eventType,
    eventTypes,
    personas,
    selectedEventType,
    title,
    description,
    selectedPersonaIds,
    errors,
    isLoadingEventTypes,
    isSubmitting,
    isCancelling,
    titlePlaceholder,
    setEventType,
    setPersonas,
    setTitle,
    setDescription,
    togglePersona,
    addNewPersona,
    handleCreate,
    handleCancel,
  };
};
