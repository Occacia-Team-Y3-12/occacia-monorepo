import axios from 'axios';
import { featureFlags } from '@/config/featureFlags';
import { mockOfferingService } from '@/mocks/vendor/offeringService';
import { API_BASE_URL } from '@/services/api';
import { Offering, CreateOfferingData, UpdateOfferingData } from '@/types/vendor/offering';
import { attachAuthHeaderInterceptor, attachVendor401Interceptor } from '@/services/http';
import { getStoredVendorToken } from '@/services/vendor/authService.shared';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

attachAuthHeaderInterceptor(api, () => getStoredVendorToken());
attachVendor401Interceptor(api);

const extractPayload = <T>(raw: unknown): T => {
  if (raw && typeof raw === 'object') {
    const record = raw as Record<string, unknown>;

    if ('data' in record && record.data !== undefined) {
      const inner = record.data;
      if (inner && typeof inner === 'object') {
        const innerRecord = inner as Record<string, unknown>;
        if ('data' in innerRecord && innerRecord.data !== undefined) {
          return innerRecord.data as T;
        }
      }
      return inner as T;
    }
  }

  return raw as T;
};

const apiOfferingService = {
  getAll: async (): Promise<Offering[]> => {
    const response = await api.get('/vendors/offerings');
    return extractPayload<Offering[]>(response.data);
  },

  getById: async (id: string): Promise<Offering> => {
    const response = await api.get(`/vendors/offerings/${id}`);
    return extractPayload<Offering>(response.data);
  },

  create: async (data: CreateOfferingData): Promise<Offering> => {
    const response = await api.post('/vendors/offerings', data);
    return extractPayload<Offering>(response.data);
  },

  update: async (id: string, data: UpdateOfferingData): Promise<Offering> => {
    const response = await api.put(`/vendors/offerings/${id}`, data);
    return extractPayload<Offering>(response.data);
  },
};

const withMockFallback = async <T>(action: () => Promise<T>, fallback: () => Promise<T>): Promise<T> => {
  try {
    return await action();
  } catch (error) {
    if (!featureFlags.enableFrontendMocks) {
      throw error;
    }
    return fallback();
  }
};

export const offeringService = featureFlags.useVendorOfferingsMock
  ? mockOfferingService
  : {
      getAll: () => withMockFallback(apiOfferingService.getAll, mockOfferingService.getAll),
      getById: (id: string) => withMockFallback(() => apiOfferingService.getById(id), () => mockOfferingService.getById(id)),
      create: (data: CreateOfferingData) => withMockFallback(() => apiOfferingService.create(data), () => mockOfferingService.create(data)),
      update: (id: string, data: UpdateOfferingData) =>
        withMockFallback(() => apiOfferingService.update(id, data), () => mockOfferingService.update(id, data)),
    };
