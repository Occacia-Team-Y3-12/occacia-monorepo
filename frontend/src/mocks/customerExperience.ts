import { EventTypeOption } from '@/types/customer';
import {
  RecommendationPackage,
  ShortlistedOffering,
} from '@/types/customer/package';

export const EVENT_TYPE_FALLBACKS: EventTypeOption[] = [
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

export const MOCK_EVENT = {
  eventTitle: 'Annual Company Gala 2026',
  eventType: 'Corporate Event',
  confirmedTasks: [
    { id: 't1', title: 'Venue Booking' },
    { id: 't2', title: 'Catering Service' },
    { id: 't3', title: 'Photography' },
    { id: 't4', title: 'Entertainment / DJ' },
  ],
};

export const createMockPackages = (): RecommendationPackage[] => [
  {
    packageId: 'pkg-budget',
    type: 'BUDGET',
    packageTotalPrice: 4200,
    currency: 'LKR',
    expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
    items: [
      { taskId: 't1', taskName: 'VENUE BOOKING', offeringId: 'b-o1', offeringTitle: 'Standard Banquet Hall', offeringCategory: 'Venue', vendorName: 'CitySpace Halls', taskPrice: 1500 },
      { taskId: 't2', taskName: 'CATERING SERVICE', offeringId: 'b-o2', offeringTitle: 'Buffet Package – Classic', offeringCategory: 'Catering', vendorName: 'QuickBite Co.', taskPrice: 1200 },
      { taskId: 't3', taskName: 'PHOTOGRAPHY', offeringId: 'b-o3', offeringTitle: '4-Hour Coverage', offeringCategory: 'Photography', vendorName: 'SnapShot Studios', taskPrice: 800 },
      { taskId: 't4', taskName: 'ENTERTAINMENT / DJ', offeringId: 'b-o4', offeringTitle: 'Basic DJ Set', offeringCategory: 'Entertainment', vendorName: 'BeatDrop DJs', taskPrice: 700 },
    ],
  },
  {
    packageId: 'pkg-recommended',
    type: 'RECOMMENDED',
    packageTotalPrice: 7850,
    currency: 'LKR',
    expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
    items: [
      { taskId: 't1', taskName: 'VENUE BOOKING', offeringId: 'r-o1', offeringTitle: 'Premier Ballroom', offeringCategory: 'Venue', vendorName: 'Grand Horizon Hotel', taskPrice: 3000 },
      { taskId: 't2', taskName: 'CATERING SERVICE', offeringId: 'r-o2', offeringTitle: "Seated Dinner – Chef's Menu", offeringCategory: 'Catering', vendorName: 'Savory & Fine', taskPrice: 2200 },
      { taskId: 't3', taskName: 'PHOTOGRAPHY', offeringId: 'r-o3', offeringTitle: 'Full-Day + Drone Coverage', offeringCategory: 'Photography', vendorName: 'Lumen Collective', taskPrice: 1500 },
      { taskId: 't4', taskName: 'ENTERTAINMENT / DJ', offeringId: 'r-o4', offeringTitle: 'DJ + MC Package', offeringCategory: 'Entertainment', vendorName: 'Vibe Nation', taskPrice: 1150 },
    ],
  },
  {
    packageId: 'pkg-highquality',
    type: 'HIGH_QUALITY',
    packageTotalPrice: 14500,
    currency: 'LKR',
    expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
    items: [
      { taskId: 't1', taskName: 'VENUE BOOKING', offeringId: 'h-o1', offeringTitle: 'Exclusive Rooftop Terrace', offeringCategory: 'Venue', vendorName: 'The Ritz Venue', taskPrice: 5500 },
      { taskId: 't2', taskName: 'CATERING SERVICE', offeringId: 'h-o2', offeringTitle: '7-Course Tasting Menu', offeringCategory: 'Catering', vendorName: 'Etoile Cuisine', taskPrice: 4200 },
      { taskId: 't3', taskName: 'PHOTOGRAPHY', offeringId: 'h-o3', offeringTitle: 'Cinematic Photo + Video', offeringCategory: 'Photography', vendorName: 'ArtFrame Studios', taskPrice: 2800 },
      { taskId: 't4', taskName: 'ENTERTAINMENT / DJ', offeringId: 'h-o4', offeringTitle: 'Live Band + DJ Fusion', offeringCategory: 'Entertainment', vendorName: 'Platinum Sounds', taskPrice: 2000 },
    ],
  },
];

export const MOCK_SHORTLIST: ShortlistedOffering[] = [
  { offeringId: 'o1', offeringTitle: 'Premium Studio', vendorName: 'Lumen Studios', taskPrice: 2500, rating: 4.9, isBestMatch: true },
  { offeringId: 'o2', offeringTitle: 'Classic Coverage', vendorName: 'SnapShot Co.', taskPrice: 1800, rating: 4.6 },
  { offeringId: 'o3', offeringTitle: 'Budget Shots', vendorName: 'QuickPic', taskPrice: 1200, rating: 4.2 },
  { offeringId: 'o4', offeringTitle: 'Drone + Ground', vendorName: 'SkyFrame', taskPrice: 3100, rating: 4.8 },
  { offeringId: 'o5', offeringTitle: 'Full Day Package', vendorName: 'ArtFrame Studios', taskPrice: 2800, rating: 4.7 },
];

export const MOCK_PACKAGE: RecommendationPackage = {
  packageId: 'pkg-001',
  type: 'RECOMMENDED',
  packageTotalPrice: 19000,
  currency: 'LKR',
  expiresAt: new Date(Date.now() + 5 * 60 * 1000).toISOString(),
  items: [
    { taskId: 't1', taskName: 'Photography', offeringId: 'o1', offeringTitle: 'Premium Studio', offeringCategory: 'Photography', vendorName: 'Lumen Studios', taskPrice: 2500, rating: 4.9 },
    { taskId: 't2', taskName: 'Catering', offeringId: 'o2', offeringTitle: "Chef's Menu", offeringCategory: 'Catering', vendorName: 'Gourmet Bites', taskPrice: 8500, rating: 4.8 },
    { taskId: 't3', taskName: 'Venue Decoration', offeringId: 'o3', offeringTitle: 'Floral Setup', offeringCategory: 'Decoration', vendorName: 'Bloom & Drape', taskPrice: 3200, rating: 4.7 },
    { taskId: 't4', taskName: 'DJ & Music', offeringId: 'o4', offeringTitle: 'DJ + MC Package', offeringCategory: 'Entertainment', vendorName: 'BeatMasters', taskPrice: 1800, rating: 4.6 },
    { taskId: 't5', taskName: 'Videography', offeringId: 'o5', offeringTitle: 'Cinematic Video', offeringCategory: 'Videography', vendorName: 'CineWed', taskPrice: 3000, rating: 4.8 },
  ],
};

export const MOCK_DRAFT_TASKS = [
  { id: 'fallback-1', title: 'Book High Tea Venue', category: 'Venue', completed: true },
  { id: 'fallback-2', title: 'Order Custom Birthday Cake', category: 'Food', completed: true },
  { id: 'fallback-3', title: 'Send Invitations', category: 'Planning', completed: true },
  { id: 'fallback-4', title: 'Buy Birthday Gift', category: 'Shopping', completed: true },
];
