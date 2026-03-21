export type PackageOrderStatus = 'CREATED' | 'COMPLETED' | 'CANCELLED_ADMIN';
export type FulfillmentRequestStatus = 'SENT' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED';
export type TaskStatus = 'DRAFT' | 'PENDING' | 'ASSIGNED' | 'IN_PROGRESS' | 'DONE' | 'REJECTED' | 'EXPIRED';

export interface PackageOrder {
  packageOrderId: string;
  eventId: string;
  packageId: string;
  packageOrderTotalPrice: number;
  currency: string;
  status: PackageOrderStatus;
  createdAt: string;
  statusUpdatedAt: string;
  idempotencyKey?: string;
}

export interface OrderTask {
  taskId: string;
  eventId: string;
  name: string;
  description?: string;
  status: TaskStatus;
  selectedOfferingId?: string;
  assignedVendorId?: string;
  expiresAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface FulfillmentRequest {
  fulfillmentRequestId: string;
  packageOrderId: string;
  taskId: string;
  vendorId: string;
  offeringId: string;
  status: FulfillmentRequestStatus;
  requestedAt: string;
  respondBy: string;
  respondedAt?: string;
  attemptNo: number;
}

export interface ConfirmPackageOrderResponse {
  packageOrder: PackageOrder;
  tasks: OrderTask[];
  fulfillmentRequests: FulfillmentRequest[];
  packageName?: string;
  eventName?: string;
  eventDate?: string;
}
