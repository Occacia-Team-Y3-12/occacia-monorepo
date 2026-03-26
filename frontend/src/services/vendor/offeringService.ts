import axios from 'axios';
import { featureFlags } from '@/config/featureFlags';
import { mockOfferingService } from '@/mocks/vendor/offeringService';
import { API_BASE_URL } from '@/services/api';
import { Offering, CreateOfferingData, UpdateOfferingData } from '@/types/vendor/offering';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('vendorToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

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

export const offeringService = featureFlags.useVendorOfferingsMock
  ? mockOfferingService
  : apiOfferingService;
