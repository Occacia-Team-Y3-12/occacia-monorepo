import type {
  RecommendationPackage,
  ShortlistedOffering,
} from '@/types/customer/package';
import type { ConfirmPackageOrderResponse } from '@/types/customer/order';

export type CustomerPackageService = {
  getPackages: (eventId: string) => Promise<RecommendationPackage[]>;
  getPackageById: (
    eventId: string,
    packageId: string
  ) => Promise<RecommendationPackage>;
  generatePackages: (eventId: string) => Promise<RecommendationPackage[]>;
  getTaskRecommendations: (
    eventId: string,
    taskId: string
  ) => Promise<ShortlistedOffering[]>;
  updatePackage: (
    eventId: string,
    packageId: string,
    items: { taskId: string; offeringId: string }[]
  ) => Promise<RecommendationPackage>;
  confirmPackage: (
    eventId: string,
    packageId: string,
    idempotencyKey: string
  ) => Promise<ConfirmPackageOrderResponse>;
  clearCachedPackages: (eventId: string) => void;
};
