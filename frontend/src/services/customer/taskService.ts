import { featureFlags } from '@/config/featureFlags';
import { mockTaskService } from '@/mocks/customer/taskService';
import { getStoredCustomerToken } from '@/services/customer/authService.shared';
import { ServiceResult } from '@/types/customer';
import {
  EventWithTasks,
  Task,
  TaskStatus,
  TaskDetails,
  ReassignTaskPayload,
  ReassignTaskResponse,
  RemoveTaskResponse,
} from '@/types/customer/task';

const JSON_HEADERS = { 'Content-Type': 'application/json' };

const withCustomerAuthHeaders = (headers?: HeadersInit) => {
  const merged = new Headers(headers);
  const token = getStoredCustomerToken();

  if (token && !merged.has('Authorization')) {
    merged.set('Authorization', `Bearer ${token}`);
  }

  return merged;
};

const request = async <T>(input: RequestInfo | URL, init?: RequestInit): Promise<ServiceResult<T>> => {
  try {
    const response = await fetch(input, {
      ...init,
      headers: withCustomerAuthHeaders(init?.headers),
    });
    const data = response.ok ? await response.json() : undefined;

    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        error: data?.message || `Request failed with status ${response.status}`,
      };
    }

    return { ok: true, status: response.status, data };
  } catch (error) {
    return {
      ok: false,
      status: 500,
      error: error instanceof Error ? error.message : 'Unexpected error occurred',
    };
  }
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const mapBackendStatusToUi = (status: unknown): TaskStatus => {
  const normalized = typeof status === 'string' ? status.toUpperCase() : '';
  switch (normalized) {
    case 'PENDING':
      return 'Pending';
    case 'ASSIGNED':
      return 'Assigned';
    case 'IN_PROGRESS':
      return 'In Progress';
    case 'REJECTED':
      return 'Rejected';
    case 'DONE':
    case 'COMPLETED':
      return 'Done';
    default:
      return 'Pending';
  }
};

const mapBackendTaskToUi = (eventId: string, value: unknown): Task | null => {
  if (!isRecord(value)) {
    return null;
  }

  const id = typeof value.taskId === 'string'
    ? value.taskId
    : typeof value.id === 'string'
      ? value.id
      : null;
  const name = typeof value.name === 'string' ? value.name : '';

  if (!id) {
    return null;
  }

  return {
    id,
    eventId,
    vendorId: typeof value.assignedVendorId === 'string' ? value.assignedVendorId : '',
    vendorName: typeof value.assignedVendorId === 'string' ? value.assignedVendorId : 'Unassigned',
    serviceType: name || 'Task',
    description: typeof value.description === 'string' ? value.description : '',
    status: mapBackendStatusToUi(value.status),
    price: typeof value.budgetMax === 'number' ? value.budgetMax : 0,
    rejectionReason: typeof value.rejectionReason === 'string' ? value.rejectionReason : undefined,
    createdAt: typeof value.createdAt === 'string' ? value.createdAt : new Date().toISOString(),
    updatedAt: typeof value.updatedAt === 'string' ? value.updatedAt : new Date().toISOString(),
  };
};

const normalizeEventWithTasks = (eventId: string, value: unknown): EventWithTasks | null => {
  if (!isRecord(value)) {
    return null;
  }

  if (Array.isArray(value.tasks)) {
    return {
      id: typeof value.id === 'string' ? value.id : eventId,
      title: typeof value.title === 'string' ? value.title : 'Event Tasks',
      eventType: typeof value.eventType === 'string' ? value.eventType : 'Other',
      status: typeof value.status === 'string' ? value.status : 'active',
      createdAt: typeof value.createdAt === 'string' ? value.createdAt : new Date().toISOString(),
      tasks: value.tasks as Task[],
    };
  }

  if (Array.isArray(value.items)) {
    const tasks = value.items
      .map((item) => mapBackendTaskToUi(eventId, item))
      .filter((task): task is Task => task !== null);

    return {
      id: eventId,
      title: 'Event Tasks',
      eventType: 'Other',
      status: 'active',
      createdAt: new Date().toISOString(),
      tasks,
    };
  }

  return null;
};

const normalizeTaskDetails = (eventId: string, value: unknown): TaskDetails | null => {
  if (!isRecord(value)) {
    return null;
  }

  if (Array.isArray(value.recommendedVendors)) {
    return value as unknown as TaskDetails;
  }

  const task = mapBackendTaskToUi(eventId, value);
  if (!task) {
    return null;
  }

  return {
    ...task,
    recommendedVendors: [],
  };
};

const apiTaskService = {
  async getEventWithTasks(eventId: string): Promise<ServiceResult<EventWithTasks>> {
    const result = await request<unknown>(`/api/v1/customers/events/${eventId}/tasks`);
    if (!result.ok) {
      return result as ServiceResult<EventWithTasks>;
    }

    const normalized = normalizeEventWithTasks(eventId, result.data);
    if (!normalized) {
      return {
        ok: false,
        status: result.status,
        error: 'Failed to parse event tasks response',
      };
    }

    return {
      ok: true,
      status: result.status,
      data: normalized,
    };
  },

  async getTaskDetails(eventId: string, taskId: string): Promise<ServiceResult<TaskDetails>> {
    const result = await request<unknown>(`/api/v1/customers/events/${eventId}/tasks/${taskId}`);
    if (!result.ok) {
      return result as ServiceResult<TaskDetails>;
    }

    const normalized = normalizeTaskDetails(eventId, result.data);
    if (!normalized) {
      return {
        ok: false,
        status: result.status,
        error: 'Failed to parse task details response',
      };
    }

    if (normalized.id !== taskId) {
      return {
        ok: false,
        status: 404,
        error: 'Task not found',
      };
    }

    return {
      ok: true,
      status: result.status,
      data: normalized,
    };
  },

  reassignTask(
    eventId: string,
    taskId: string,
    payload: ReassignTaskPayload
  ): Promise<ServiceResult<ReassignTaskResponse>> {
    return request<ReassignTaskResponse>(`/api/v1/customers/events/${eventId}/tasks/${taskId}/reassign`, {
      method: 'POST',
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    });
  },

  removeTask(eventId: string, taskId: string): Promise<ServiceResult<RemoveTaskResponse>> {
    return request<RemoveTaskResponse>(`/api/v1/customers/events/${eventId}/tasks/${taskId}`, {
      method: 'DELETE',
    });
  },
};

export const taskService =
  featureFlags.enableFrontendMocks || featureFlags.useCustomerPlanningMockApi
    ? mockTaskService
    : apiTaskService;
