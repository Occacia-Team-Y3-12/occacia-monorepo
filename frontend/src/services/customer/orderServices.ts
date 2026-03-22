import axios from 'axios';

import { featureFlags } from '@/config/featureFlags';
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

const mockCustomerOrderService = {
  async listOrders(): Promise<PackageOrder[]> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    if (typeof window === 'undefined') {
      return [];
    }

    const orders: PackageOrder[] = [];
    for (const key of Object.keys(sessionStorage)) {
      if (!key.startsWith('order_')) {
        continue;
      }

      const raw = sessionStorage.getItem(key);
      if (!raw) {
        continue;
      }

      try {
        const parsed = JSON.parse(raw) as { packageOrder?: PackageOrder };
        if (parsed.packageOrder) {
          orders.push(parsed.packageOrder);
        }
      } catch {
        continue;
      }
    }

    return orders.sort((left, right) =>
      right.createdAt.localeCompare(left.createdAt)
    );
  },
};

export const customerOrderService = featureFlags.useCustomerOrdersMock
  ? mockCustomerOrderService
  : apiCustomerOrderService;
