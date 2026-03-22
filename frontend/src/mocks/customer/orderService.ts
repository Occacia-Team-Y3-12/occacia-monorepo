import type { PackageOrder } from '@/types/customer/order';

export const mockCustomerOrderService = {
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
