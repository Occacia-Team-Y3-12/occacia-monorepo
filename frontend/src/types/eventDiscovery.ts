export type EventCategory =
  | 'Conference'
  | 'Workshop'
  | 'Festival'
  | 'Networking'
  | 'Wellness'
  | 'Exhibition';

export type EventPriceType = 'Free' | 'Paid';

export type EventSortOption = 'newest' | 'upcoming' | 'popular';

export type EventDateFilter = 'all' | 'week' | 'month' | 'quarter';

export interface EventRecord {
  id: string;
  title: string;
  description: string;
  category: EventCategory;
  priceType: EventPriceType;
  priceLabel: string;
  location: string;
  city: string;
  startsAt: string;
  publishedAt: string;
  popularityScore: number;
  image: {
    src: string;
    alt: string;
  };
}

export interface EventFiltersState {
  query: string;
  category: 'all' | EventCategory;
  date: EventDateFilter;
  location: 'all' | string;
  priceType: 'all' | EventPriceType;
  sort: EventSortOption;
}
