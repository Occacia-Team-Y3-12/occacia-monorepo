export type QualityTier = 'BUDGET' | 'STANDARD' | 'PREMIUM' | 'LUXURY';
export type OfferingCategory = 'CATERING' | 'PHOTOGRAPHY' | 'VENUE' | 'DECORATION' | 'MUSIC' | 'TRANSPORT' | 'OTHER';

export interface Offering {
  id: string;
  vendorId: string;
  title: string;
  description: string;
  category: OfferingCategory;
  price: number;
  qualityTier: QualityTier;
  isActive: boolean;
  isAvailable: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateOfferingData {
  title: string;
  description: string;
  category: OfferingCategory;
  price: number;
  qualityTier: QualityTier;
  isActive: boolean;
  isAvailable: boolean;
}

export type UpdateOfferingData = Partial<CreateOfferingData>;
