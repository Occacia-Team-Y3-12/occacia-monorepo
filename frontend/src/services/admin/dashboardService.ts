import { api } from '@/services/api';
import type { AdminDashboardMetricsResponse, HealthStatusResponse } from '@/types/admin';

export const dashboardService = {
  async getAdminDashboardMetrics(): Promise<AdminDashboardMetricsResponse> {
    const { data } = await api.get<AdminDashboardMetricsResponse>('/admin/dashboard');
    return data;
  },

  async getHealthStatus(): Promise<HealthStatusResponse> {
    const { data } = await api.get<HealthStatusResponse>('/health');
    return data;
  },
};
