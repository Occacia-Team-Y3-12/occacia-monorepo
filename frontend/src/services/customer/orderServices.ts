import { API_BASE_URL } from '@/services/api';
import type { PackageOrder } from '@/types/customer/order';

const readOrdersFromSession = (): PackageOrder[] => {
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
};

const fetchOrdersFromApi = async (): Promise<PackageOrder[] | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/customers/package-orders`, {
      headers:
        typeof window !== 'undefined'
          ? {
              Authorization: `Bearer ${localStorage.getItem('customerToken') || ''}`,
            }
          : undefined,
      cache: 'no-store',
    });

    if (!response.ok) {
      return null;
    }

    const body = (await response.json()) as
      | PackageOrder[]
      | { items?: PackageOrder[] };
    if (Array.isArray(body)) {
      return body;
    }
    if (Array.isArray(body.items)) {
      return body.items;
    }
    return null;
  } catch {
    return null;
  }
};

export const customerOrderService = {
  async listOrders(): Promise<PackageOrder[]> {
    const apiOrders = await fetchOrdersFromApi();
    if (apiOrders && apiOrders.length > 0) {
      return apiOrders;
    }

    return readOrdersFromSession();
  },
};

