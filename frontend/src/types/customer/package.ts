export type PackageType = 'BUDGET' | 'RECOMMENDED' | 'HIGH_QUALITY';

export interface ShortlistedOffering {
  offeringId: string;
  offeringTitle: string;
  vendorName: string;
  taskPrice: number;
  rating: number;
  isBestMatch?: boolean;
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
  type: PackageType;
  packageTotalPrice: number;
  currency: string;
  items: PackageItem[];
  expiresAt: string;
}
