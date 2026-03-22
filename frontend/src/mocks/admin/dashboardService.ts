import type {
  AdminDashboardMetricsResponse,
  HealthStatusResponse,
} from '@/types/admin';

export const mockDashboardService = {
  async getAdminDashboardMetrics(): Promise<AdminDashboardMetricsResponse> {
    await new Promise((resolve) => setTimeout(resolve, 200));

    return {
      users: { total: 126, active: 92, pending: 11 },
      vendors: { total: 48, active: 31, pending: 9 },
      events: { total: 67, active: 54, pending: 7 },
      packageOrders: { total: 24, active: 16, pending: 5 },
      generatedAt: new Date().toISOString(),
    };
  },

  async getHealthStatus(): Promise<HealthStatusResponse> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    return {
      status: 'healthy',
      system: 'mock',
      version: 'frontend-mock',
      uptimeSeconds: 86400,
    };
  },
};
