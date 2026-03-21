import { apiClient } from '@/lib/api';
import { TaskListResponse, TaskDetail, TaskStatus, TaskPriority } from '@/types/vendorTasks';

interface TaskFilters {
  status?: TaskStatus;
  priority?: TaskPriority;
  search?: string;
  date_from?: string;
  date_to?: string;
}

export const vendorTaskApi = {
  getTasks: async (filters?: TaskFilters): Promise<TaskListResponse> => {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.search) params.append('search', filters.search);
    if (filters?.date_from) params.append('date_from', filters.date_from);
    if (filters?.date_to) params.append('date_to', filters.date_to);
    
    const response = await apiClient.get(`/vendors/tasks?${params.toString()}`);
    return response.data;
  },

  getTaskDetail: async (taskId: number): Promise<TaskDetail> => {
    const response = await apiClient.get(`/vendors/tasks/${taskId}`);
    return response.data;
  },

  getDashboardStats: async () => {
    const response = await apiClient.get('/vendors/tasks/stats/dashboard');
    return response.data;
  }
};