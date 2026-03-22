import type { EventTypeOption } from '@/types/customer';
import { EVENT_TYPE_FALLBACKS } from '@/mocks/customerExperience';

export const CURATED_EVENT_TYPES: EventTypeOption[] = [
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
    id: 'other',
    value: 'others',
    label: 'Other',
    example: 'Appointment',
    titlePlaceholder: 'e.g., Doctor appointment this Saturday',
  },
];

export const getEventTypeKey = (type: Pick<EventTypeOption, 'value' | 'label'>) => {
  const normalizedValue = String(type.value || '').trim().toLowerCase();
  const normalizedLabel = String(type.label || '').trim().toLowerCase();
  const source = normalizedValue || normalizedLabel;

  if (source === 'individual') return 'individual';
  if (source === 'group') return 'group';
  if (source === 'other' || source === 'others') return 'other';
  return '';
};

export const normalizeEventTypes = (types: EventTypeOption[]) => {
  const map = new Map<string, EventTypeOption>();

  CURATED_EVENT_TYPES.forEach((type) => {
    map.set(getEventTypeKey(type), type);
  });

  types.forEach((type) => {
    const key = getEventTypeKey(type);
    if (!key) return;

    map.set(key, {
      ...type,
      id: key,
      value: key === 'other' ? 'others' : key,
      label: key === 'other' ? 'Other' : key === 'group' ? 'Group' : 'Individual',
    });
  });

  return ['individual', 'group', 'other']
    .map((key) => map.get(key))
    .filter((type): type is EventTypeOption => Boolean(type));
};

export const getFallbackEventTypes = () => normalizeEventTypes(EVENT_TYPE_FALLBACKS);
