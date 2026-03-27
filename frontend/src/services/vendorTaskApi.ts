import axios, { AxiosError } from 'axios';
import { featureFlags } from '@/config/featureFlags';
import { mockVendorTaskApi } from '@/mocks/vendor/vendorTaskApi';
import { TaskListResponse, TaskListItem } from '@/types/vendorTasks';
import { attachVendor401Interceptor } from '@/services/http';

type VendorTaskStatus = 'ASSIGNED' | 'IN_PROGRESS' | 'DONE' | string;
type FulfillmentDecision = 'ACCEPT' | 'REJECT';

export interface FulfillmentRequestItem {
  fulfillmentRequestId: string;
  packageOrderId: string;
  taskId: string;
  vendorId: string;
  offeringId: string;
  status: string;
  requestedAt: string;
  respondBy: string | null;
  respondedAt: string | null;
  responseNote: string | null;
  attemptNo: number;
}

export interface VendorTaskItem {
  taskId: string;
  eventId: string;
  name: string;
  description: string | null;
  quantity: number;
  needsVendor: boolean;
  vendorCategory: string | null;
  budgetMin: number | null;
  budgetMax: number | null;
  currency: string;
  status: VendorTaskStatus;
  selectedOfferingId: string | null;
  assignedVendorId: string | null;
  confirmedAt: string | null;
  lockedAt: string | null;
  dueAt: string | null;
  expiresAt: string | null;
  rejectedAt: string | null;
  rejectionReason: string | null;
  statusUpdatedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

interface PaginatedResponse<T> {
  items: T[];
  nextCursor: string | null;
}

interface RespondFulfillmentResponse {
  fulfillmentRequest: FulfillmentRequestItem;
  task: VendorTaskItem;
}

interface UpdateVendorTaskPayload {
  status: 'IN_PROGRESS' | 'DONE';
  note?: string;
}

interface GetTasksFilters {
  search?: string;
  priority?: 'high' | 'medium' | 'low';
}

function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (!configured) {
    return '/api/v1';
  }
  return configured.endsWith('/api/v1') ? configured : `${configured}/api/v1`;
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const parts = token.split('.');
  if (parts.length < 2) {
    return null;
  }
  try {
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const normalized = payload.padEnd(payload.length + ((4 - (payload.length % 4)) % 4), '=');
    const decoded = atob(normalized);
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function isVendorToken(token: string | null): token is string {
  if (!token) {
    return false;
  }
  const payload = decodeJwtPayload(token);
  const role = String(payload?.role ?? '').toUpperCase();
  return role === 'VENDOR';
}

function getAuthToken(): string | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const preferred = localStorage.getItem('vendorToken');
  if (isVendorToken(preferred)) {
    return preferred;
  }

  const candidates = [
    localStorage.getItem('access_token'),
    localStorage.getItem('accessToken'),
    localStorage.getItem('auth_token'),
  ];
  const vendorCandidate = candidates.find((token) => isVendorToken(token));
  return vendorCandidate ?? null;
}

function mapTaskStatusToLegacy(status: VendorTaskStatus): TaskListItem['status'] {
  const normalized = String(status).toUpperCase();
  if (normalized === 'ASSIGNED') return 'assigned';
  if (normalized === 'IN_PROGRESS') return 'assigned';
  if (normalized === 'DONE') return 'completed';
  return 'assigned';
}

function inferLegacyPriority(task: Pick<VendorTaskItem, 'budgetMax' | 'budgetMin'>): TaskListItem['priority'] {
  const maxBudget = task.budgetMax ?? task.budgetMin ?? 0;
  if (maxBudget >= 5000) return 'high';
  if (maxBudget >= 2500) return 'medium';
  return 'low';
}

function mapTaskToLegacy(task: VendorTaskItem): TaskListItem {
  const dueDate = task.dueAt ?? task.expiresAt;
  return {
    id: Number.parseInt(task.taskId, 10) || 0,
    title: task.name,
    status: mapTaskStatusToLegacy(task.status),
    priority: inferLegacyPriority(task),
    due_date: dueDate ?? undefined,
    expiry_date: task.expiresAt ?? undefined,
    budget_range:
      task.budgetMin !== null && task.budgetMax !== null
        ? `${task.currency} ${task.budgetMin} - ${task.budgetMax}`
        : undefined,
    customer: {
      id: 0,
      name: 'Customer',
      email: 'hidden@occacia.local',
    },
    event: task.eventId
      ? {
          id: 0,
          title: `Event ${task.eventId}`,
          occasion_type: task.vendorCategory ?? 'General',
          event_date: task.createdAt,
        }
      : undefined,
    created_at: task.createdAt,
    is_urgent: false,
  };
}

function mapAxiosError(error: unknown, fallback: string): Error {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
    const detail = axiosError.response?.data?.detail ?? axiosError.response?.data?.message;
    return new Error(detail || fallback);
  }
  if (error instanceof Error) {
    return error;
  }
  return new Error(fallback);
}

const vendorApi = axios.create({
  baseURL: getApiBaseUrl(),
  headers: { 'Content-Type': 'application/json' },
});

vendorApi.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
attachVendor401Interceptor(vendorApi);

const apiVendorTaskApi = {
  async getFulfillmentRequests(params?: {
    status?: string;
    limit?: number;
    cursor?: string;
  }): Promise<PaginatedResponse<FulfillmentRequestItem>> {
    try {
      const response = await vendorApi.get<PaginatedResponse<FulfillmentRequestItem>>(
        '/vendors/fulfillment-requests',
        {
          params: {
            status: params?.status ?? 'SENT',
            limit: params?.limit ?? 50,
            cursor: params?.cursor,
          },
        }
      );
      return response.data;
    } catch (error) {
      throw mapAxiosError(error, 'Failed to load fulfillment requests');
    }
  },

  async respondToFulfillmentRequest(
    fulfillmentRequestId: string,
    payload: { decision: FulfillmentDecision; responseNote?: string }
  ): Promise<RespondFulfillmentResponse> {
    try {
      const response = await vendorApi.post<RespondFulfillmentResponse>(
        `/vendors/fulfillment-requests/${fulfillmentRequestId}/response`,
        {
          decision: payload.decision,
          responseNote: payload.responseNote,
        }
      );
      return response.data;
    } catch (error) {
      throw mapAxiosError(error, 'Failed to submit request response');
    }
  },

  async getVendorTasks(params?: {
    status?: string;
    limit?: number;
    cursor?: string;
  }): Promise<PaginatedResponse<VendorTaskItem>> {
    try {
      const response = await vendorApi.get<PaginatedResponse<VendorTaskItem>>('/vendors/tasks', {
        params: {
          status: params?.status,
          limit: params?.limit ?? 100,
          cursor: params?.cursor,
        },
      });
      return response.data;
    } catch (error) {
      throw mapAxiosError(error, 'Failed to load vendor tasks');
    }
  },

  async updateVendorTaskStatus(taskId: string, payload: UpdateVendorTaskPayload): Promise<VendorTaskItem> {
    try {
      const response = await vendorApi.put<VendorTaskItem>(`/vendors/tasks/${taskId}`, payload);
      return response.data;
    } catch (error) {
      throw mapAxiosError(error, 'Failed to update task status');
    }
  },

  // Compatibility method used by legacy Vendor Activities page.
  async getTasks(_filters?: GetTasksFilters): Promise<TaskListResponse> {
    const [pendingRequests, vendorTasks] = await Promise.all([
      this.getFulfillmentRequests({ status: 'SENT', limit: 100 }),
      this.getVendorTasks({ limit: 100 }),
    ]);

    const assigned = vendorTasks.items.filter((task) => {
      const normalized = String(task.status).toUpperCase();
      return normalized === 'ASSIGNED' || normalized === 'IN_PROGRESS';
    });
    const completed = vendorTasks.items.filter(
      (task) => String(task.status).toUpperCase() === 'DONE'
    );

    const rejectedOrExpired: TaskListItem[] = [];
    pendingRequests.items.forEach((request) => {
      const normalized = String(request.status).toUpperCase();
      if (normalized === 'REJECTED' || normalized === 'EXPIRED') {
        rejectedOrExpired.push({
          id: Number.parseInt(request.fulfillmentRequestId, 10) || 0,
          title: `Request ${request.fulfillmentRequestId}`,
          status: normalized === 'EXPIRED' ? 'expired' : 'rejected',
          priority: 'medium',
          due_date: undefined,
          expiry_date: request.respondBy ?? undefined,
          budget_range: undefined,
          customer: { id: 0, name: 'Customer', email: 'hidden@occacia.local' },
          event: undefined,
          created_at: request.requestedAt,
          is_urgent: false,
        });
      }
    });

    return {
      pending_response: pendingRequests.items.map((request) => ({
        id: Number.parseInt(request.fulfillmentRequestId, 10) || 0,
        title: `Request ${request.fulfillmentRequestId}`,
        status: 'pending_response',
        priority: 'medium',
        due_date: undefined,
        expiry_date: request.respondBy ?? undefined,
        budget_range: undefined,
        customer: { id: 0, name: 'Customer', email: 'hidden@occacia.local' },
        event: undefined,
        created_at: request.requestedAt,
        is_urgent: false,
      })),
      assigned: assigned.map(mapTaskToLegacy),
      completed: completed.map(mapTaskToLegacy),
      rejected_expired: rejectedOrExpired,
      total_count: pendingRequests.items.length + vendorTasks.items.length + rejectedOrExpired.length,
    };
  },
};

export const vendorTaskApi = featureFlags.useVendorTasksMock
  ? mockVendorTaskApi
  : apiVendorTaskApi;
