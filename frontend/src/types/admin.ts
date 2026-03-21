export enum CustomerAccountStatus {
  ACTIVE = 'ACTIVE',
  PENDING = 'PENDING',
  SUSPENDED = 'SUSPENDED',
  DISABLED = 'DISABLED',
}

export interface AdminCustomer {
  customer_id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  locale?: string | null;
  status: CustomerAccountStatus;
}

export interface PaginatedCustomersResponse {
  items: AdminCustomer[];
  nextCursor?: string | null;
}

export interface UpdateCustomerStatusRequest {
  status: CustomerAccountStatus;
}
