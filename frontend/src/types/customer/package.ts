export type PackageType = 'BUDGET' | 'RECOMMENDED' | 'HIGH_QUALITY';

export interface PackageItem {
  taskId: string;
  taskName: string;
  offeringTitle: string;
  offeringCategory: string;
  vendorName: string;
  taskPrice: number;
  isAvailable?: boolean;
}

export interface RecommendationPackage {
  packageId: string;
  type: PackageType;
  packageTotalPrice: number;
  currency: string;
  items: PackageItem[];
  expiresAt: string;
}
