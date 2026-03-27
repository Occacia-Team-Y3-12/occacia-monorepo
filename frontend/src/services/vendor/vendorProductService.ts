import axios from 'axios';

import { featureFlags } from '@/config/featureFlags';
import { mockVendorProductService } from '@/mocks/vendor/vendorProductService';
import { API_BASE_URL } from '@/services/api';
import type {
  CreateVendorProductData,
  UpdateVendorProductData,
  VendorProduct,
} from '@/types/vendor/product';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('vendorToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }

  return config;
});

const extractPayload = <T>(raw: unknown): T => {
  if (raw && typeof raw === 'object') {
    const record = raw as Record<string, unknown>;
    if ('data' in record && record.data !== undefined) {
      const nested = record.data;
      if (nested && typeof nested === 'object') {
        const nestedRecord = nested as Record<string, unknown>;
        if ('data' in nestedRecord && nestedRecord.data !== undefined) {
          return nestedRecord.data as T;
        }
      }
      return nested as T;
    }
  }

  return raw as T;
};

const apiVendorProductService = {
  getAll: async (): Promise<VendorProduct[]> => {
    const response = await api.get('/vendors/products');
    return extractPayload<VendorProduct[]>(response.data);
  },

  create: async (data: CreateVendorProductData): Promise<VendorProduct> => {
    const response = await api.post('/vendors/products', data);
    return extractPayload<VendorProduct>(response.data);
  },

  update: async (id: string, data: UpdateVendorProductData): Promise<VendorProduct> => {
    const response = await api.put(`/vendors/products/${id}`, data);
    return extractPayload<VendorProduct>(response.data);
  },

  toggleActive: async (id: string): Promise<VendorProduct> => {
    const response = await api.patch(`/vendors/products/${id}/status`);
    return extractPayload<VendorProduct>(response.data);
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

export const vendorProductService = featureFlags.useVendorProductsMock
  ? mockVendorProductService
  : {
      getAll: () => withMockFallback(apiVendorProductService.getAll, mockVendorProductService.getAll),
      create: (data: CreateVendorProductData) =>
        withMockFallback(() => apiVendorProductService.create(data), () => mockVendorProductService.create(data)),
      update: (id: string, data: UpdateVendorProductData) =>
        withMockFallback(() => apiVendorProductService.update(id, data), () => mockVendorProductService.update(id, data)),
      toggleActive: (id: string) =>
        withMockFallback(() => apiVendorProductService.toggleActive(id), () => mockVendorProductService.toggleActive(id)),
    };
