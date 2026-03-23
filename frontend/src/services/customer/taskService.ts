import { featureFlags } from '@/config/featureFlags';
import { mockTaskService } from '@/mocks/customer/taskService';
import { getStoredCustomerToken } from '@/services/customer/authService.shared';
import { ServiceResult } from '@/types/customer';
import {
  EventWithTasks,
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

const apiTaskService = {
  getEventWithTasks(eventId: string): Promise<ServiceResult<EventWithTasks>> {
    return request<EventWithTasks>(`/api/v1/customers/events/${eventId}/tasks`);
  },

  getTaskDetails(eventId: string, taskId: string): Promise<ServiceResult<TaskDetails>> {
    return request<TaskDetails>(`/api/v1/customers/events/${eventId}/tasks/${taskId}`);
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
