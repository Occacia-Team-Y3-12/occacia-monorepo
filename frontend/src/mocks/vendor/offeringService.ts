import type {
  CreateOfferingData,
  Offering,
  UpdateOfferingData,
} from '@/types/vendor/offering';

const MOCK_OFFERINGS_KEY = 'occacia_vendor_offerings_mock';

const seedOfferings: Offering[] = [
  {
    id: 'off-101',
    vendorId: 'mock-vendor-1',
    title: 'Signature Evening Catering',
    description: 'A plated catering package for intimate evening celebrations.',
    category: 'CATERING',
    price: 4500,
    qualityTier: 'PREMIUM',
    isActive: true,
    isAvailable: true,
    createdAt: new Date(Date.now() - 10 * 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 3 * 86400000).toISOString(),
  },
  {
    id: 'off-102',
    vendorId: 'mock-vendor-1',
    title: 'Editorial Event Photography',
    description: 'Half-day photography coverage with edited gallery delivery.',
    category: 'PHOTOGRAPHY',
    price: 3200,
    qualityTier: 'STANDARD',
    isActive: true,
    isAvailable: true,
    createdAt: new Date(Date.now() - 15 * 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 5 * 86400000).toISOString(),
  },
];

function loadMockOfferings(): Offering[] {
  if (typeof window === 'undefined') {
    return seedOfferings;
  }

  const stored = localStorage.getItem(MOCK_OFFERINGS_KEY);
  if (!stored) {
    localStorage.setItem(MOCK_OFFERINGS_KEY, JSON.stringify(seedOfferings));
    return seedOfferings;
  }

  try {
    return JSON.parse(stored) as Offering[];
  } catch {
    localStorage.setItem(MOCK_OFFERINGS_KEY, JSON.stringify(seedOfferings));
    return seedOfferings;
  }
}

function persistMockOfferings(offerings: Offering[]) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(MOCK_OFFERINGS_KEY, JSON.stringify(offerings));
  }
}

export const mockOfferingService = {
  getAll: async (): Promise<Offering[]> => {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return loadMockOfferings().sort((left, right) =>
      right.updatedAt.localeCompare(left.updatedAt)
    );
  },

  getById: async (id: string): Promise<Offering> => {
    await new Promise((resolve) => setTimeout(resolve, 120));

    const offering = loadMockOfferings().find((item) => item.id === id);
    if (!offering) {
      throw new Error('Offering not found.');
    }

    return offering;
  },

  create: async (data: CreateOfferingData): Promise<Offering> => {
    await new Promise((resolve) => setTimeout(resolve, 180));

    const offerings = loadMockOfferings();
    const nextOffering: Offering = {
      id: `off-${Date.now()}`,
      vendorId: 'mock-vendor-1',
      ...data,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    persistMockOfferings([nextOffering, ...offerings]);
    return nextOffering;
  },

  update: async (id: string, data: UpdateOfferingData): Promise<Offering> => {
    await new Promise((resolve) => setTimeout(resolve, 180));

    const offerings = loadMockOfferings();
    const index = offerings.findIndex((item) => item.id === id);
    if (index < 0) {
      throw new Error('Offering not found.');
    }

    offerings[index] = {
      ...offerings[index],
      ...data,
      updatedAt: new Date().toISOString(),
    };

    persistMockOfferings(offerings);
    return offerings[index];
  },
};
