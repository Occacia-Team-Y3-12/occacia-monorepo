import axios from 'axios';

import { API_BASE_URL } from '@/services/api';
import type {
  PackageItem,
  RecommendationPackage,
  ShortlistedOffering,
} from '@/types/customer/package';
import type { CustomerPackageService } from './packageService.types';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('customerToken');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const normalizePackageItem = (raw: unknown): PackageItem | null => {
  if (!isRecord(raw)) {
    return null;
  }

  if (
    typeof raw.taskId !== 'string'
    || typeof raw.taskName !== 'string'
    || typeof raw.offeringId !== 'string'
  ) {
    return null;
  }

  return {
    taskId: raw.taskId,
    taskName: raw.taskName,
    offeringId: raw.offeringId,
    offeringTitle:
      typeof raw.offeringTitle === 'string'
        ? raw.offeringTitle
        : typeof raw.offeringName === 'string'
          ? raw.offeringName
          : 'Offering',
    offeringCategory: typeof raw.offeringCategory === 'string' ? raw.offeringCategory : 'General',
    vendorName: typeof raw.vendorName === 'string' && raw.vendorName.trim() ? raw.vendorName : 'Vendor',
    taskPrice: typeof raw.taskPrice === 'number' ? raw.taskPrice : 0,
  };
};

const normalizePackage = (raw: unknown): RecommendationPackage | null => {
  if (!isRecord(raw)) {
    return null;
  }

  if (
    typeof raw.packageId !== 'string'
    || typeof raw.packageType !== 'string'
    || typeof raw.packageTotalPrice !== 'number'
  ) {
    return null;
  }

  const items = Array.isArray(raw.items)
    ? raw.items
      .map(normalizePackageItem)
      .filter((item): item is PackageItem => item !== null)
    : [];

  const packageType = raw.packageType;
  const normalizedType =
    packageType === 'BUDGET' || packageType === 'RECOMMENDED' || packageType === 'HIGH_QUALITY'
      ? packageType
      : 'RECOMMENDED';

  return {
    packageId: raw.packageId,
    type: normalizedType,
    packageTotalPrice: raw.packageTotalPrice,
    currency: typeof raw.currency === 'string' ? raw.currency : 'LKR',
    items,
    expiresAt:
      typeof raw.expiresAt === 'string'
        ? raw.expiresAt
        : new Date(Date.now() + 5 * 60 * 1000).toISOString(),
  };
};

const normalizePackageList = (raw: unknown): RecommendationPackage[] => {
  if (Array.isArray(raw)) {
    return raw
      .map(normalizePackage)
      .filter((pkg): pkg is RecommendationPackage => pkg !== null);
  }

  if (isRecord(raw) && Array.isArray(raw.packages)) {
    return raw.packages
      .map(normalizePackage)
      .filter((pkg): pkg is RecommendationPackage => pkg !== null);
  }

  return [];
};

const normalizeTaskRecommendations = (raw: unknown): ShortlistedOffering[] => {
  if (!Array.isArray(raw)) {
    return [];
  }

  return raw
    .filter(isRecord)
    .map((item) => {
      const offeringId = typeof item.offeringId === 'string' ? item.offeringId : '';
      const offeringTitle =
        typeof item.name === 'string'
          ? item.name
          : typeof item.offeringTitle === 'string'
            ? item.offeringTitle
            : 'Offering';
      const vendorName = typeof item.vendorName === 'string' && item.vendorName.trim()
        ? item.vendorName
        : 'Vendor';
      const taskPrice =
        typeof item.price === 'number'
          ? item.price
          : typeof item.taskPrice === 'number'
            ? item.taskPrice
            : 0;
      const score = typeof item.score === 'number' ? item.score : undefined;
      const rank = typeof item.rank === 'number' ? item.rank : undefined;

      const normalizedRating =
        typeof score === 'number' ? Math.min(5, Math.max(0, Number((score / 4).toFixed(1)))) : undefined;

      return {
        offeringId,
        offeringTitle,
        vendorName,
        vendorId: typeof item.vendorId === 'string' ? item.vendorId : undefined,
        taskPrice,
        currency: typeof item.currency === 'string' ? item.currency : undefined,
        qualityTier: typeof item.qualityTier === 'string' ? item.qualityTier : undefined,
        score,
        rank,
        rating: normalizedRating,
        isBestMatch: rank === 1,
        isSelected: typeof item.isSelected === 'boolean' ? item.isSelected : undefined,
        description: typeof item.description === 'string' ? item.description : undefined,
        unit: typeof item.unit === 'string' ? item.unit : undefined,
      };
    })
    .filter((item) => !!item.offeringId);
};

export const apiPackageService: CustomerPackageService = {
  getPackages: (eventId) =>
    api
      .get(`/customers/events/${eventId}/packages`)
      .then((response) => normalizePackageList(response.data)),

  getPackageById: (eventId, packageId) =>
    api
      .get(`/customers/events/${eventId}/packages/${packageId}`)
      .then((response) => {
        const normalized = normalizePackage(response.data);
        if (!normalized) {
          throw new Error('Invalid package response');
        }
        return normalized;
      }),

  generatePackages: (eventId) =>
    api
      .post(`/customers/events/${eventId}/recommendations`)
      .then((response) => normalizePackageList(response.data)),

  getTaskRecommendations: (eventId, taskId) =>
    api
      .get(`/customers/events/${eventId}/tasks/${taskId}/offerings`)
      .then((response) => normalizeTaskRecommendations(response.data.items ?? response.data)),

  updatePackage: (eventId, packageId, items) =>
    api
      .put(`/customers/events/${eventId}/packages/${packageId}`, { items })
      .then((response) => {
        const normalized = normalizePackage(response.data);
        if (!normalized) {
          throw new Error('Invalid package response');
        }
        return normalized;
      }),

  confirmPackage: (eventId, packageId, idempotencyKey) =>
    api
      .post(
        `/customers/events/${eventId}/packages/${packageId}/confirm`,
        {},
        { headers: { 'Idempotency-Key': idempotencyKey } }
      )
      .then((response) => response.data),

  clearCachedPackages: () => {},
};
