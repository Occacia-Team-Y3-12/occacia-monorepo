export type PackageType = 'BUDGET' | 'RECOMMENDED' | 'HIGH_QUALITY';

export interface ShortlistedOffering {
  offeringId: string;
  offeringTitle: string;
  vendorName: string;
  vendorId?: string;
  taskPrice: number;
  currency?: string;
  qualityTier?: string;
  score?: number;
  rank?: number;
  rating?: number;
  isBestMatch?: boolean;
  isSelected?: boolean;
  description?: string;
  unit?: string;
}

export interface PackageItem {
  taskId: string;
  taskName: string;
  offeringId: string;
  offeringTitle: string;
  offeringCategory: string;
  vendorName: string;
  taskPrice: number;
  rating?: number;
  isAvailable?: boolean;
  shortlist?: ShortlistedOffering[];
}

export interface RecommendationPackage {
  packageId: string;
  name?: string;
  type: PackageType;
  packageTotalPrice: number;
  currency: string;
  items: PackageItem[];
  expiresAt: string;
  eventName?: string;
  eventDate?: string;
  eventLocation?: string;
}
