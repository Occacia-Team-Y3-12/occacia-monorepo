import { featureFlags } from '@/config/featureFlags';
import { ServiceResult } from '@/types/customer';
import {
  EventWithTasks,
  TaskDetails,
  ReassignTaskPayload,
  ReassignTaskResponse,
  RemoveTaskResponse,
} from '@/types/customer/task';

const JSON_HEADERS = { 'Content-Type': 'application/json' };

const request = async <T>(input: RequestInfo | URL, init?: RequestInit): Promise<ServiceResult<T>> => {
  try {
    const response = await fetch(input, init);
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

const mockEventWithTasks: EventWithTasks = {
  id: 'evt-track-1',
  title: 'Mock Celebration Event',
  eventType: 'Birthday',
  status: 'active',
  createdAt: new Date(Date.now() - 7 * 86400000).toISOString(),
  tasks: [
    {
      id: 'task-1',
      eventId: 'evt-track-1',
      vendorId: 'vendor-1',
      vendorName: 'Lumen Studios',
      serviceType: 'Photography',
      description: 'Half-day photography package',
      status: 'Assigned',
      price: 2200,
      createdAt: new Date(Date.now() - 6 * 86400000).toISOString(),
      updatedAt: new Date(Date.now() - 2 * 86400000).toISOString(),
    },
    {
      id: 'task-2',
      eventId: 'evt-track-1',
      vendorId: 'vendor-2',
      vendorName: 'Golden Table',
      serviceType: 'Catering',
      description: 'Garden dinner catering',
      status: 'Rejected',
      price: 3400,
      rejectionReason: 'Selected menu was unavailable.',
      createdAt: new Date(Date.now() - 5 * 86400000).toISOString(),
      updatedAt: new Date(Date.now() - 86400000).toISOString(),
    },
  ],
};

function buildTaskDetails(taskId: string): TaskDetails | null {
  const task = mockEventWithTasks.tasks.find((item) => item.id === taskId);
  if (!task) {
    return null;
  }

  return {
    ...task,
    recommendedVendors: [
      {
        vendorId: 'vendor-3',
        vendorName: 'Gather Co.',
        rating: 4.9,
        price: task.price + 250,
      },
      {
        vendorId: 'vendor-4',
        vendorName: 'North Studio',
        rating: 4.7,
        price: task.price - 150,
      },
    ],
  };
}

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

const mockTaskService = {
  async getEventWithTasks(eventId: string): Promise<ServiceResult<EventWithTasks>> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    return {
      ok: true,
      status: 200,
      data: {
        ...mockEventWithTasks,
        id: eventId,
        tasks: mockEventWithTasks.tasks.map((task) => ({ ...task, eventId })),
      },
    };
  },

  async getTaskDetails(
    _eventId: string,
    taskId: string
  ): Promise<ServiceResult<TaskDetails>> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    const details = buildTaskDetails(taskId);
    if (!details) {
      return {
        ok: false,
        status: 404,
        error: 'Task not found',
      };
    }

    return {
      ok: true,
      status: 200,
      data: details,
    };
  },

  async reassignTask(
    _eventId: string,
    taskId: string,
    payload: ReassignTaskPayload
  ): Promise<ServiceResult<ReassignTaskResponse>> {
    await new Promise((resolve) => setTimeout(resolve, 160));

    const task = mockEventWithTasks.tasks.find((item) => item.id === taskId);
    if (!task) {
      return {
        ok: false,
        status: 404,
        error: 'Task not found',
      };
    }

    task.vendorId = payload.newVendorId;
    task.vendorName =
      buildTaskDetails(taskId)?.recommendedVendors.find(
        (vendor) => vendor.vendorId === payload.newVendorId
      )?.vendorName ?? 'Reassigned Vendor';
    task.status = 'Assigned';
    task.rejectionReason = undefined;
    task.updatedAt = new Date().toISOString();

    return {
      ok: true,
      status: 200,
      data: {
        status: 'success',
        message: 'Task reassigned successfully.',
        data: {
          taskId,
          status: task.status,
        },
      },
    };
  },

  async removeTask(
    _eventId: string,
    taskId: string
  ): Promise<ServiceResult<RemoveTaskResponse>> {
    await new Promise((resolve) => setTimeout(resolve, 120));

    mockEventWithTasks.tasks = mockEventWithTasks.tasks.filter(
      (task) => task.id !== taskId
    );

    return {
      ok: true,
      status: 200,
      data: {
        status: 'success',
        message: 'Task removed successfully.',
      },
    };
  },
};

export const taskService =
  featureFlags.enableFrontendMocks || featureFlags.useCustomerPlanningMockApi
    ? mockTaskService
    : apiTaskService;
