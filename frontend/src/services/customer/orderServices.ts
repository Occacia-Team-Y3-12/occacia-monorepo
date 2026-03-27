import axios from 'axios';

import { featureFlags } from '@/config/featureFlags';
import { mockCustomerOrderService } from '@/mocks/customer/orderService';
import { API_BASE_URL } from '@/services/api';
import type { PackageOrder } from '@/types/customer/order';
import { attachAuthHeaderInterceptor, attachCustomer401Interceptor } from '@/services/http';
import { getStoredCustomerToken } from '@/services/customer/authService.shared';

const api = axios.create({
  baseURL: API_BASE_URL,
});

attachAuthHeaderInterceptor(api, () => getStoredCustomerToken());
attachCustomer401Interceptor(api);

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
