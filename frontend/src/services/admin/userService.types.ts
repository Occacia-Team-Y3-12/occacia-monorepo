import {
  AdminCustomer,
  CustomerAccountStatus,
  PaginatedCustomersResponse,
  UpdateCustomerStatusRequest,
} from '@/types/admin';

export interface CustomerListParams {
  status?: CustomerAccountStatus;
  limit?: number;
  cursor?: string;
}

export interface CustomerUserService {
  getCustomers: (
    params?: CustomerListParams
  ) => Promise<PaginatedCustomersResponse>;
  getCustomerById: (customerId: string) => Promise<AdminCustomer>;
  updateCustomerStatus: (
    customerId: string,
    payload: UpdateCustomerStatusRequest
  ) => Promise<AdminCustomer>;
}
