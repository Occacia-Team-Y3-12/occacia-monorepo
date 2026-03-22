import axios from 'axios';

import { featureFlags } from '@/config/featureFlags';
import { mockCustomerOrderService } from '@/mocks/customer/orderService';
import { API_BASE_URL } from '@/services/api';
import type { PackageOrder } from '@/types/customer/order';

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('customerToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const apiCustomerOrderService = {
  async listOrders(): Promise<PackageOrder[]> {
    const response = await api.get<{ items: PackageOrder[] }>(
      '/customers/package-orders'
    );

    return response.data.items ?? [];
  },
};

export const customerOrderService = featureFlags.useCustomerOrdersMock
  ? mockCustomerOrderService
  : apiCustomerOrderService;
