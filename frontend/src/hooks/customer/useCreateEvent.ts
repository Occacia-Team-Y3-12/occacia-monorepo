'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { customerEventService } from '@/services/customer/eventServices';
import { ROUTES } from '@/lib/routes';
import { CreateCustomerEventPayload, CustomerEventType, CustomerPersonaOption } from '@/types/customer';

const DEFAULT_EVENT_TYPE: CustomerEventType = 'individual';

const TITLE_PLACEHOLDERS: Record<CustomerEventType, string> = {
  individual: "e.g., Sarah's 30th Birthday Bash",
  group: 'e.g., Team Appreciation Evening',
  others: 'e.g., Community Celebration Night',
};

export const PERSONA_OPTIONS: CustomerPersonaOption[] = [
  { id: 'john-cena', name: 'John Cena', role: 'Professional Athlete' },
  { id: 'sarah-jenkins', name: 'Sarah Jenkins', role: 'Corporate Client' },
  { id: 'michael-chen', name: 'Michael Chen', role: 'Vendor Manager' },
];

export const useCreateEvent = () => {
  const router = useRouter();
  const [eventType, setEventType] = useState<CustomerEventType>(DEFAULT_EVENT_TYPE);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>([]);
  const [errors, setErrors] = useState<{ eventType?: string; title?: string; form?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const titlePlaceholder = useMemo(() => TITLE_PLACEHOLDERS[eventType], [eventType]);

  const togglePersona = (personaId: string) => {
    setSelectedPersonaIds((prev) =>
      prev.includes(personaId) ? prev.filter((id) => id !== personaId) : [...prev, personaId]
    );
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
        personaIds: selectedPersonaIds,
      };

      const result = await customerEventService.createDraftEvent(payload);

      if (!result.ok || !result.data?.data?.eventId) {
        setErrors({ form: result.data?.message || 'Unable to create event. Please try again.' });
        return;
      }

      const eventId = result.data.data.eventId;
      router.push(ROUTES.CUSTOMER.EVENT_CHAT(eventId));
    } catch {
      setErrors({ form: 'Something went wrong while creating the event.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    router.push(ROUTES.CUSTOMER.DASHBOARD);
  };

  return {
    eventType,
    title,
    description,
    selectedPersonaIds,
    errors,
    isSubmitting,
    titlePlaceholder,
    setEventType,
    setTitle,
    setDescription,
    togglePersona,
    handleCreate,
    handleCancel,
  };
};
