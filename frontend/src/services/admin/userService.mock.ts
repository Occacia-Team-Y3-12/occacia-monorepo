import {
  AdminCustomer,
  CustomerAccountStatus,
  PaginatedCustomersResponse,
  UpdateCustomerStatusRequest,
} from '@/types/admin';

import { CustomerListParams, CustomerUserService } from './userService.types';

const MOCK_STORAGE_KEY = 'occacia_admin_customers_mock';

const seedCustomers: AdminCustomer[] = [
  {
    customer_id: 'CUS-0001',
    email: 'amelia.perera@occacia.dev',
    full_name: 'Amelia Perera',
    phone: '+94 77 123 4567',
    locale: 'en',
    status: CustomerAccountStatus.ACTIVE,
  },
  {
    customer_id: 'CUS-0002',
    email: 'nimal.silva@occacia.dev',
    full_name: 'Nimal Silva',
    phone: '+94 71 987 6543',
    locale: 'en',
    status: CustomerAccountStatus.PENDING,
  },
  {
    customer_id: 'CUS-0003',
    email: 'safiya.hassan@occacia.dev',
    full_name: 'Safiya Hassan',
    phone: '+94 76 456 1200',
    locale: 'ar',
    status: CustomerAccountStatus.SUSPENDED,
  },
  {
    customer_id: 'CUS-0004',
    email: 'kavindu.jayasuriya@occacia.dev',
    full_name: 'Kavindu Jayasuriya',
    phone: null,
    locale: 'en',
    status: CustomerAccountStatus.DISABLED,
  },
];

function loadCustomers(): AdminCustomer[] {
  if (typeof window === 'undefined') {
    return seedCustomers;
  }

  const stored = window.localStorage.getItem(MOCK_STORAGE_KEY);
  if (!stored) {
    window.localStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(seedCustomers));
    return seedCustomers;
  }

  try {
    return JSON.parse(stored) as AdminCustomer[];
  } catch {
    window.localStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(seedCustomers));
    return seedCustomers;
  }
}

function persistCustomers(customers: AdminCustomer[]) {
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(MOCK_STORAGE_KEY, JSON.stringify(customers));
  }
}

export const mockUserService: CustomerUserService = {
  getCustomers: async (
    params: CustomerListParams = {}
  ): Promise<PaginatedCustomersResponse> => {
    const allCustomers = loadCustomers();
    const filteredCustomers = params.status
      ? allCustomers.filter((customer) => customer.status === params.status)
      : allCustomers;

    const startIndex = params.cursor
      ? Math.max(
          0,
          filteredCustomers.findIndex(
            (customer) => customer.customer_id === params.cursor
          ) + 1
        )
      : 0;
    const limit = params.limit ?? 20;
    const items = filteredCustomers.slice(startIndex, startIndex + limit);
    const nextCursor =
      startIndex + limit < filteredCustomers.length
        ? items[items.length - 1]?.customer_id ?? null
        : null;

    return {
      items,
      nextCursor,
    };
  },

  getCustomerById: async (customerId: string): Promise<AdminCustomer> => {
    const customer = loadCustomers().find(
      (item) => item.customer_id === customerId
    );

    if (!customer) {
      throw new Error(`Mock customer not found: ${customerId}`);
    }

    return customer;
  },

  updateCustomerStatus: async (
    customerId: string,
    payload: UpdateCustomerStatusRequest
  ): Promise<AdminCustomer> => {
    const customers = loadCustomers();
    const index = customers.findIndex((item) => item.customer_id === customerId);

    if (index < 0) {
      throw new Error(`Mock customer not found: ${customerId}`);
    }

    const updatedCustomer = {
      ...customers[index],
      status: payload.status,
    };
    customers[index] = updatedCustomer;
    persistCustomers(customers);

    return updatedCustomer;
  },
};
