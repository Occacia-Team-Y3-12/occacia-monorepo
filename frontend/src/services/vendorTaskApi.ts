import axios, { AxiosError } from 'axios';
import { featureFlags } from '@/config/featureFlags';
import { TaskListResponse, TaskListItem } from '@/types/vendorTasks';

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

const MOCK_REQUESTS_KEY = 'occacia_vendor_fulfillment_requests_mock';
const MOCK_TASKS_KEY = 'occacia_vendor_tasks_mock';

const seedFulfillmentRequests: FulfillmentRequestItem[] = [
  {
    fulfillmentRequestId: '301',
    packageOrderId: 'order-9001',
    taskId: '401',
    vendorId: 'mock-vendor-1',
    offeringId: 'off-101',
    status: 'SENT',
    requestedAt: new Date(Date.now() - 90 * 60000).toISOString(),
    respondBy: new Date(Date.now() + 3 * 60 * 60000).toISOString(),
    respondedAt: null,
    responseNote: null,
    attemptNo: 1,
  },
  {
    fulfillmentRequestId: '302',
    packageOrderId: 'order-9002',
    taskId: '402',
    vendorId: 'mock-vendor-1',
    offeringId: 'off-102',
    status: 'SENT',
    requestedAt: new Date(Date.now() - 30 * 60000).toISOString(),
    respondBy: new Date(Date.now() + 5 * 60 * 60000).toISOString(),
    respondedAt: null,
    responseNote: null,
    attemptNo: 2,
  },
];

const seedVendorTasks: VendorTaskItem[] = [
  {
    taskId: '501',
    eventId: 'evt-101',
    name: 'Venue lighting setup',
    description: 'Install warm lighting before guest arrival.',
    quantity: 1,
    needsVendor: true,
    vendorCategory: 'Lighting',
    budgetMin: 2000,
    budgetMax: 3800,
    currency: 'USD',
    status: 'ASSIGNED',
    selectedOfferingId: 'off-101',
    assignedVendorId: 'mock-vendor-1',
    confirmedAt: new Date(Date.now() - 86400000).toISOString(),
    lockedAt: new Date(Date.now() - 86400000).toISOString(),
    dueAt: new Date(Date.now() + 86400000).toISOString(),
    expiresAt: null,
    rejectedAt: null,
    rejectionReason: null,
    statusUpdatedAt: new Date(Date.now() - 86400000).toISOString(),
    createdAt: new Date(Date.now() - 2 * 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    taskId: '502',
    eventId: 'evt-102',
    name: 'Photography coverage',
    description: 'Capture ceremony and dinner moments.',
    quantity: 1,
    needsVendor: true,
    vendorCategory: 'Photography',
    budgetMin: 4200,
    budgetMax: 6200,
    currency: 'USD',
    status: 'IN_PROGRESS',
    selectedOfferingId: 'off-102',
    assignedVendorId: 'mock-vendor-1',
    confirmedAt: new Date(Date.now() - 2 * 86400000).toISOString(),
    lockedAt: new Date(Date.now() - 2 * 86400000).toISOString(),
    dueAt: new Date(Date.now() + 2 * 86400000).toISOString(),
    expiresAt: null,
    rejectedAt: null,
    rejectionReason: null,
    statusUpdatedAt: new Date(Date.now() - 2 * 3600000).toISOString(),
    createdAt: new Date(Date.now() - 3 * 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 3600000).toISOString(),
  },
  {
    taskId: '503',
    eventId: 'evt-103',
    name: 'Custom dessert bar',
    description: 'Dessert station delivered and arranged on site.',
    quantity: 1,
    needsVendor: true,
    vendorCategory: 'Catering',
    budgetMin: 1800,
    budgetMax: 2200,
    currency: 'USD',
    status: 'DONE',
    selectedOfferingId: 'off-101',
    assignedVendorId: 'mock-vendor-1',
    confirmedAt: new Date(Date.now() - 5 * 86400000).toISOString(),
    lockedAt: new Date(Date.now() - 5 * 86400000).toISOString(),
    dueAt: new Date(Date.now() - 2 * 86400000).toISOString(),
    expiresAt: null,
    rejectedAt: null,
    rejectionReason: null,
    statusUpdatedAt: new Date(Date.now() - 86400000).toISOString(),
    createdAt: new Date(Date.now() - 6 * 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 86400000).toISOString(),
  },
];

const sleep = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

function loadMockCollection<T>(key: string, fallback: T[]): T[] {
  if (typeof window === 'undefined') {
    return fallback;
  }

  const stored = localStorage.getItem(key);
  if (!stored) {
    localStorage.setItem(key, JSON.stringify(fallback));
    return fallback;
  }

  try {
    return JSON.parse(stored) as T[];
  } catch {
    localStorage.setItem(key, JSON.stringify(fallback));
    return fallback;
  }
}

function persistMockCollection<T>(key: string, items: T[]) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(key, JSON.stringify(items));
  }
}

function paginateItems<T>(
  items: T[],
  limit: number,
  cursor: string | undefined,
  selectId: (item: T) => string
): PaginatedResponse<T> {
  const startIndex = cursor
    ? Math.max(0, items.findIndex((item) => selectId(item) === cursor) + 1)
    : 0;
  const paginatedItems = items.slice(startIndex, startIndex + limit);
  const nextCursor =
    startIndex + limit < items.length
      ? selectId(paginatedItems[paginatedItems.length - 1])
      : null;

  return {
    items: paginatedItems,
    nextCursor,
  };
}

function createMockTaskFromRequest(request: FulfillmentRequestItem): VendorTaskItem {
  return {
    taskId: request.taskId,
    eventId: `evt-${request.taskId}`,
    name: `Accepted task ${request.taskId}`,
    description: 'Mock task created from accepted fulfillment request.',
    quantity: 1,
    needsVendor: true,
    vendorCategory: 'General',
    budgetMin: 2500,
    budgetMax: 4200,
    currency: 'USD',
    status: 'ASSIGNED',
    selectedOfferingId: request.offeringId,
    assignedVendorId: request.vendorId,
    confirmedAt: new Date().toISOString(),
    lockedAt: new Date().toISOString(),
    dueAt: new Date(Date.now() + 2 * 86400000).toISOString(),
    expiresAt: null,
    rejectedAt: null,
    rejectionReason: null,
    statusUpdatedAt: new Date().toISOString(),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

function buildPendingLegacyItem(
  request: FulfillmentRequestItem
): TaskListItem {
  const isUrgent =
    request.respondBy !== null &&
    new Date(request.respondBy).getTime() - Date.now() < 2 * 3600000;

  return {
    id: Number.parseInt(request.fulfillmentRequestId, 10) || 0,
    title: `Request ${request.fulfillmentRequestId}`,
    status: 'pending_response',
    priority: request.attemptNo > 1 ? 'high' : 'medium',
    due_date: undefined,
    expiry_date: request.respondBy ?? undefined,
    budget_range: undefined,
    customer: { id: 0, name: 'Customer', email: 'hidden@occacia.local' },
    event: undefined,
    created_at: request.requestedAt,
    is_urgent: isUrgent,
  };
}

function filterLegacyTasks(
  items: TaskListItem[],
  filters?: GetTasksFilters
): TaskListItem[] {
  return items.filter((item) => {
    if (
      filters?.search?.trim() &&
      !item.title.toLowerCase().includes(filters.search.trim().toLowerCase())
    ) {
      return false;
    }

    if (filters?.priority && item.priority !== filters.priority) {
      return false;
    }

    return true;
  });
}

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

const mockVendorTaskApi = {
  async getFulfillmentRequests(params?: {
    status?: string;
    limit?: number;
    cursor?: string;
  }): Promise<PaginatedResponse<FulfillmentRequestItem>> {
    await sleep(150);

    const items = loadMockCollection(MOCK_REQUESTS_KEY, seedFulfillmentRequests)
      .filter((request) =>
        params?.status
          ? String(request.status).toUpperCase() === params.status.toUpperCase()
          : true
      )
      .sort((left, right) => right.requestedAt.localeCompare(left.requestedAt));

    return paginateItems(
      items,
      params?.limit ?? 50,
      params?.cursor,
      (item) => item.fulfillmentRequestId
    );
  },

  async respondToFulfillmentRequest(
    fulfillmentRequestId: string,
    payload: { decision: FulfillmentDecision; responseNote?: string }
  ): Promise<RespondFulfillmentResponse> {
    await sleep(180);

    const requests = loadMockCollection(MOCK_REQUESTS_KEY, seedFulfillmentRequests);
    const tasks = loadMockCollection(MOCK_TASKS_KEY, seedVendorTasks);
    const requestIndex = requests.findIndex(
      (request) => request.fulfillmentRequestId === fulfillmentRequestId
    );

    if (requestIndex < 0) {
      throw new Error('Mock fulfillment request not found');
    }

    const updatedRequest: FulfillmentRequestItem = {
      ...requests[requestIndex],
      status: payload.decision === 'ACCEPT' ? 'ACCEPTED' : 'REJECTED',
      respondedAt: new Date().toISOString(),
      responseNote: payload.responseNote ?? null,
    };
    requests[requestIndex] = updatedRequest;
    persistMockCollection(MOCK_REQUESTS_KEY, requests);

    let task =
      tasks.find((item) => item.taskId === updatedRequest.taskId) ??
      createMockTaskFromRequest(updatedRequest);

    if (payload.decision === 'ACCEPT') {
      const existingIndex = tasks.findIndex((item) => item.taskId === task.taskId);
      task = {
        ...task,
        status: 'ASSIGNED',
        statusUpdatedAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      if (existingIndex >= 0) {
        tasks[existingIndex] = task;
      } else {
        tasks.unshift(task);
      }
      persistMockCollection(MOCK_TASKS_KEY, tasks);
    }

    return {
      fulfillmentRequest: updatedRequest,
      task,
    };
  },

  async getVendorTasks(params?: {
    status?: string;
    limit?: number;
    cursor?: string;
  }): Promise<PaginatedResponse<VendorTaskItem>> {
    await sleep(150);

    const items = loadMockCollection(MOCK_TASKS_KEY, seedVendorTasks)
      .filter((task) =>
        params?.status
          ? String(task.status).toUpperCase() === params.status.toUpperCase()
          : true
      )
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));

    return paginateItems(
      items,
      params?.limit ?? 100,
      params?.cursor,
      (item) => item.taskId
    );
  },

  async updateVendorTaskStatus(
    taskId: string,
    payload: UpdateVendorTaskPayload
  ): Promise<VendorTaskItem> {
    await sleep(180);

    const tasks = loadMockCollection(MOCK_TASKS_KEY, seedVendorTasks);
    const index = tasks.findIndex((task) => task.taskId === taskId);
    if (index < 0) {
      throw new Error('Mock vendor task not found');
    }

    tasks[index] = {
      ...tasks[index],
      status: payload.status,
      statusUpdatedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    persistMockCollection(MOCK_TASKS_KEY, tasks);

    return tasks[index];
  },

  async getTasks(filters?: GetTasksFilters): Promise<TaskListResponse> {
    const [pendingRequests, vendorTasks] = await Promise.all([
      this.getFulfillmentRequests({ status: 'SENT', limit: 100 }),
      this.getVendorTasks({ limit: 100 }),
    ]);

    const assigned = filterLegacyTasks(
      vendorTasks.items
        .filter((task) => {
          const normalized = String(task.status).toUpperCase();
          return normalized === 'ASSIGNED' || normalized === 'IN_PROGRESS';
        })
        .map(mapTaskToLegacy),
      filters
    );

    const completed = filterLegacyTasks(
      vendorTasks.items
        .filter((task) => String(task.status).toUpperCase() === 'DONE')
        .map(mapTaskToLegacy),
      filters
    );

    const pending = filterLegacyTasks(
      pendingRequests.items.map(buildPendingLegacyItem),
      filters
    );

    return {
      pending_response: pending,
      assigned,
      completed,
      rejected_expired: [],
      total_count: pending.length + assigned.length + completed.length,
    };
  },
};

export const vendorTaskApi = featureFlags.useVendorTasksMock
  ? mockVendorTaskApi
  : apiVendorTaskApi;
