import type { EventFiltersState, EventRecord } from '@/types/eventDiscovery';

const weekdayFormatter = new Intl.DateTimeFormat('en-US', { weekday: 'short' });
const monthDayFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
});
const timeFormatter = new Intl.DateTimeFormat('en-US', {
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
});

function parseDate(value: string): Date {
  return new Date(value);
}

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function endOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0, 23, 59, 59, 999);
}

function endOfWeek(date: Date): Date {
  const day = date.getDay();
  const diffToSunday = (7 - day) % 7;
  return new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate() + diffToSunday,
    23,
    59,
    59,
    999,
  );
}

function addMonths(date: Date, months: number): Date {
  return new Date(
    date.getFullYear(),
    date.getMonth() + months,
    date.getDate(),
    23,
    59,
    59,
    999,
  );
}

function compareAsc(left: Date, right: Date): number {
  return left.getTime() - right.getTime();
}

function compareDesc(left: Date, right: Date): number {
  return right.getTime() - left.getTime();
}

export const mockEvents: EventRecord[] = [
  {
    id: 'midnight-sessions',
    title: 'Midnight Sessions',
    description:
      'An intimate after-hours design forum with live critiques, visual installations, and a vinyl-backed lounge set.',
    category: 'Conference',
    priceType: 'Paid',
    priceLabel: 'LKR 120',
    location: 'The Glasshouse',
    city: 'New York, NY',
    startsAt: '2026-04-04T19:30:00.000Z',
    publishedAt: '2026-02-24T09:00:00.000Z',
    popularityScore: 98,
    image: {
      src: '/images/customer/events/discovery/midnight-sessions.svg',
      alt: 'Editorial poster for Midnight Sessions',
    },
  },
  {
    id: 'field-notes-live',
    title: 'Field Notes Live',
    description:
      'A creative strategy workshop built around real campaign teardowns, founder storytelling, and brand worldbuilding.',
    category: 'Workshop',
    priceType: 'Paid',
    priceLabel: 'LKR 85',
    location: 'Atlas Studio',
    city: 'Austin, TX',
    startsAt: '2026-03-29T15:00:00.000Z',
    publishedAt: '2026-03-10T13:45:00.000Z',
    popularityScore: 91,
    image: {
      src: '/images/customer/events/discovery/field-notes-live.svg',
      alt: 'Poster artwork for Field Notes Live',
    },
  },
  {
    id: 'rooftop-frequency',
    title: 'Rooftop Frequency',
    description:
      'Golden-hour networking for product leaders, operators, and founders with a panoramic skyline backdrop.',
    category: 'Networking',
    priceType: 'Free',
    priceLabel: 'Free Entry',
    location: 'Crescent Rooftop',
    city: 'Chicago, IL',
    startsAt: '2026-04-12T23:00:00.000Z',
    publishedAt: '2026-03-04T11:20:00.000Z',
    popularityScore: 87,
    image: {
      src: '/images/customer/events/discovery/rooftop-frequency.svg',
      alt: 'Poster artwork for Rooftop Frequency',
    },
  },
  {
    id: 'slow-form-weekend',
    title: 'Slow Form Weekend',
    description:
      'A restorative wellness retreat with breathwork, sound baths, and a tactile ritual-led morning program.',
    category: 'Wellness',
    priceType: 'Paid',
    priceLabel: 'LKR 140',
    location: 'Luma House',
    city: 'Los Angeles, CA',
    startsAt: '2026-05-02T17:00:00.000Z',
    publishedAt: '2026-02-18T15:10:00.000Z',
    popularityScore: 76,
    image: {
      src: '/images/customer/events/discovery/slow-form-weekend.svg',
      alt: 'Poster artwork for Slow Form Weekend',
    },
  },
  {
    id: 'future-matter',
    title: 'Future Matter Expo',
    description:
      'A multi-sensory exhibition featuring immersive tech prototypes, material labs, and artist-engineer collaborations.',
    category: 'Exhibition',
    priceType: 'Paid',
    priceLabel: 'LKR 45',
    location: 'Harbor Pavilion',
    city: 'San Francisco, CA',
    startsAt: '2026-04-18T18:00:00.000Z',
    publishedAt: '2026-03-15T08:30:00.000Z',
    popularityScore: 95,
    image: {
      src: '/images/customer/events/discovery/future-matter.svg',
      alt: 'Poster artwork for Future Matter Expo',
    },
  },
  {
    id: 'summer-commons',
    title: 'Summer Commons',
    description:
      'A city-scale cultural festival blending food pop-ups, independent music, and experimental public installations.',
    category: 'Festival',
    priceType: 'Free',
    priceLabel: 'Free Entry',
    location: 'Riverfront Park',
    city: 'Seattle, WA',
    startsAt: '2026-06-07T20:00:00.000Z',
    publishedAt: '2026-03-01T12:00:00.000Z',
    popularityScore: 89,
    image: {
      src: '/images/customer/events/discovery/slow-form-weekend.svg',
      alt: 'Poster artwork for Summer Commons',
    },
  },
  {
    id: 'signal-dinner',
    title: 'Signal Dinner Series',
    description:
      'An invitation-only tasting and conversation evening bringing together founders, curators, and media voices.',
    category: 'Networking',
    priceType: 'Paid',
    priceLabel: 'LKR 160',
    location: 'Maison North',
    city: 'Boston, MA',
    startsAt: '2026-04-09T22:30:00.000Z',
    publishedAt: '2026-03-20T10:15:00.000Z',
    popularityScore: 82,
    image: {
      src: '/images/customer/events/discovery/midnight-sessions.svg',
      alt: 'Poster artwork for Signal Dinner Series',
    },
  },
  {
    id: 'makers-assembly',
    title: 'Makers Assembly',
    description:
      'A practical build-day for creators and indie teams focused on shipping polished ideas in public.',
    category: 'Workshop',
    priceType: 'Free',
    priceLabel: 'Free Entry',
    location: 'Foundry Hall',
    city: 'Denver, CO',
    startsAt: '2026-03-27T16:00:00.000Z',
    publishedAt: '2026-03-18T09:40:00.000Z',
    popularityScore: 73,
    image: {
      src: '/images/customer/events/discovery/field-notes-live.svg',
      alt: 'Poster artwork for Makers Assembly',
    },
  },
  {
    id: 'lightwell-stories',
    title: 'Lightwell Stories',
    description:
      'A storytelling salon on brand, identity, and modern hospitality with a cinematic visual program.',
    category: 'Conference',
    priceType: 'Paid',
    priceLabel: 'LKR 95',
    location: 'Mercer Annex',
    city: 'Miami, FL',
    startsAt: '2026-04-25T21:00:00.000Z',
    publishedAt: '2026-03-12T16:20:00.000Z',
    popularityScore: 90,
    image: {
      src: '/images/customer/events/discovery/future-matter.svg',
      alt: 'Poster artwork for Lightwell Stories',
    },
  },
  {
    id: 'kinetic-mornings',
    title: 'Kinetic Mornings',
    description:
      'A design-forward wellness social with guided movement, coffee rituals, and soundtrack-led transitions.',
    category: 'Wellness',
    priceType: 'Free',
    priceLabel: 'Free Entry',
    location: 'Drift Courtyard',
    city: 'Portland, OR',
    startsAt: '2026-04-02T14:00:00.000Z',
    publishedAt: '2026-03-21T07:50:00.000Z',
    popularityScore: 79,
    image: {
      src: '/images/customer/events/discovery/rooftop-frequency.svg',
      alt: 'Poster artwork for Kinetic Mornings',
    },
  },
];

export const defaultEventFilters: EventFiltersState = {
  query: '',
  category: 'all',
  date: 'all',
  location: 'all',
  priceType: 'all',
  sort: 'upcoming',
};

export const eventCategories: Array<'all' | EventRecord['category']> = [
  'all',
  ...new Set(mockEvents.map((event) => event.category)),
];

export const eventLocations = ['all', ...new Set(mockEvents.map((event) => event.city))];

export function formatEventDateLabel(startsAt: string): string {
  const date = parseDate(startsAt);
  return `${weekdayFormatter.format(date)}, ${monthDayFormatter.format(date)} - ${timeFormatter.format(date)}`;
}

function matchesDateFilter(startsAt: string, filter: EventFiltersState['date']): boolean {
  const eventDate = parseDate(startsAt);
  const now = startOfDay(new Date());

  if (eventDate.getTime() < now.getTime()) {
    return false;
  }

  switch (filter) {
    case 'week':
      return compareAsc(eventDate, endOfWeek(now)) <= 0;
    case 'month':
      return compareAsc(eventDate, endOfMonth(now)) <= 0;
    case 'quarter':
      return compareAsc(eventDate, addMonths(now, 3)) <= 0;
    case 'all':
    default:
      return true;
  }
}

export function getFilteredAndSortedEvents(
  events: EventRecord[],
  filters: EventFiltersState,
): EventRecord[] {
  const filtered = events.filter((event) => {
    const normalizedQuery = filters.query.trim().toLowerCase();
    const matchesQuery =
      normalizedQuery.length === 0 ||
      event.title.toLowerCase().includes(normalizedQuery) ||
      event.description.toLowerCase().includes(normalizedQuery);

    const matchesCategory =
      filters.category === 'all' || event.category === filters.category;
    const matchesLocation =
      filters.location === 'all' || event.city === filters.location;
    const matchesPrice =
      filters.priceType === 'all' || event.priceType === filters.priceType;
    const matchesDate = matchesDateFilter(event.startsAt, filters.date);

    return (
      matchesQuery &&
      matchesCategory &&
      matchesLocation &&
      matchesPrice &&
      matchesDate
    );
  });

  return filtered.sort((left, right) => {
    switch (filters.sort) {
      case 'newest':
        return compareDesc(parseDate(left.publishedAt), parseDate(right.publishedAt));
      case 'popular':
        return right.popularityScore - left.popularityScore;
      case 'upcoming':
      default:
        return compareAsc(parseDate(left.startsAt), parseDate(right.startsAt));
    }
  });
}
