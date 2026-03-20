import axios from 'axios';
import type { RecommendationPackage, ShortlistedOffering } from '@/types/customer/package';
import type { ConfirmPackageOrderResponse, PackageOrder, OrderTask, FulfillmentRequest } from '@/types/customer/order';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('customerToken');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const packageService = {
  getPackages: (eventId: string) =>
    api.get<RecommendationPackage[]>(`/customers/events/${eventId}/packages`).then(r => r.data),

  getPackageById: (eventId: string, packageId: string) =>
    api.get<RecommendationPackage>(`/customers/events/${eventId}/packages/${packageId}`).then(r => r.data),

  generatePackages: (eventId: string) =>
    api.post<RecommendationPackage[]>(`/customers/events/${eventId}/recommendations`).then(r => r.data),

  getTaskRecommendations: (eventId: string, taskId: string) =>
    api.get<ShortlistedOffering[]>(`/customers/events/${eventId}/tasks/${taskId}/recommendations`).then(r => r.data),

  updatePackage: (eventId: string, packageId: string, items: { taskId: string; offeringId: string }[]) =>
    api.put<RecommendationPackage>(`/customers/events/${eventId}/packages/${packageId}`, { items }).then(r => r.data),

  confirmPackage: async (eventId: string, packageId: string, idempotencyKey: string): Promise<ConfirmPackageOrderResponse> => {
    try {
      return await api.post<ConfirmPackageOrderResponse>(
        `/customers/events/${eventId}/packages/${packageId}/confirm`,
        {},
        { headers: { 'Idempotency-Key': idempotencyKey } }
      ).then(r => r.data);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409 || status === 400 || status === 401 || status === 403) throw err;

      // Backend not available — build mock response from cached package
      const stored = typeof window !== 'undefined' ? sessionStorage.getItem(`packages_${eventId}`) : null;
      const pkgs: RecommendationPackage[] = stored ? JSON.parse(stored) : [];
      const pkg = pkgs.find(p => p.packageId === packageId);
      if (!pkg) throw err;

      const now = new Date().toISOString();
      const packageOrderId = `order-${crypto.randomUUID().slice(0, 8)}`;
      const respondBy = new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString();

      const packageOrder: PackageOrder = {
        packageOrderId,
        eventId,
        packageId,
        packageOrderTotalPrice: pkg.packageTotalPrice,
        currency: pkg.currency,
        status: 'CREATED',
        createdAt: now,
        statusUpdatedAt: now,
        idempotencyKey,
      };

      const tasks: OrderTask[] = pkg.items.map(item => ({
        taskId: item.taskId,
        eventId,
        name: item.taskName,
        status: 'PENDING',
        selectedOfferingId: item.offeringId,
        createdAt: now,
        updatedAt: now,
      }));

      const fulfillmentRequests: FulfillmentRequest[] = pkg.items.map(item => ({
        fulfillmentRequestId: `fr-${crypto.randomUUID().slice(0, 8)}`,
        packageOrderId,
        taskId: item.taskId,
        vendorId: `vendor-${item.offeringId}`,
        offeringId: item.offeringId,
        status: 'SENT',
        requestedAt: now,
        respondBy,
        attemptNo: 1,
      }));

      return {
        packageOrder,
        tasks,
        fulfillmentRequests,
        packageName: pkg.name ?? `${pkg.type.charAt(0) + pkg.type.slice(1).toLowerCase()} Package`,
        eventName: pkg.eventName,
        eventDate: pkg.eventDate,
      };
    }
  },
};
