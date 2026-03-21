import { api } from '@/services/api';
import {
  AdminCustomer,
  CustomerAccountStatus,
  PaginatedCustomersResponse,
  UpdateCustomerStatusRequest,
} from '@/types/admin';

interface CustomerListParams {
  status?: CustomerAccountStatus;
  limit?: number;
  cursor?: string;
}

export const userService = {
  getCustomers: async (
    params: CustomerListParams = {}
  ): Promise<PaginatedCustomersResponse> => {
    const { data } = await api.get('/admin/customers', { params });
    return data;
  },

  getCustomerById: async (customerId: string): Promise<AdminCustomer> => {
    const { data } = await api.get(`/admin/customers/${customerId}`);
    return data;
  },

  updateCustomerStatus: async (
    customerId: string,
    payload: UpdateCustomerStatusRequest
  ): Promise<AdminCustomer> => {
    const { data } = await api.put(
      `/admin/customers/${customerId}/status`,
      payload
    );
    return data;
  },
};
