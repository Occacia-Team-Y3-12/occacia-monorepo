export type PackageOrderStatus =
  | 'CREATED'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'CANCELLED_ADMIN'
  | 'CANCELLED_CUSTOMER';

export type TaskOrderStatus =
  | 'PENDING'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'IN_PROGRESS'
  | 'COMPLETED';

export type FulfillmentRequestStatus =
  | 'SENT'
  | 'PENDING'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'EXPIRED';

export type PackageOrder = {
  packageOrderId: string;
  eventId: string;
  packageId: string;
  packageOrderTotalPrice: number;
  currency: string;
  status: PackageOrderStatus;
  createdAt: string;
  statusUpdatedAt: string;
  idempotencyKey?: string;
};

export type OrderTask = {
  taskId: string;
  eventId: string;
  name: string;
  status: TaskOrderStatus | string;
  selectedOfferingId?: string | null;
  createdAt: string;
  updatedAt: string;
};

export type FulfillmentRequest = {
  fulfillmentRequestId: string;
  packageOrderId: string;
  taskId: string;
  vendorId: string;
  offeringId: string;
  status: FulfillmentRequestStatus | string;
  requestedAt: string;
  respondBy?: string | null;
  respondedAt?: string | null;
  responseNote?: string | null;
  attemptNo: number;
};

export type ConfirmPackageOrderResponse = {
  packageOrder: PackageOrder;
  tasks: OrderTask[];
  fulfillmentRequests: FulfillmentRequest[];
  packageName?: string;
  eventName?: string;
  eventDate?: string;
};

