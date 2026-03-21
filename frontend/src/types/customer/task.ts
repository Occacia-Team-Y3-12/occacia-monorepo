export type TaskStatus = 'Pending' | 'Assigned' | 'In Progress' | 'Rejected' | 'Done';

export interface Task {
  id: string;
  eventId: string;
  vendorId: string;
  vendorName: string;
  vendorLogo?: string;
  serviceType: string;
  description: string;
  status: TaskStatus;
  price: number;
  rejectionReason?: string;
  createdAt: string;
  updatedAt: string;
}

export interface VendorShortlist {
  vendorId: string;
  vendorName: string;
  vendorLogo?: string;
  rating: number;
  price: number;
}

export interface TaskDetails extends Task {
  recommendedVendors: VendorShortlist[];
}

export interface ReassignTaskPayload {
  newVendorId: string;
}

export interface ReassignTaskResponse {
  status: 'success' | 'error';
  message: string;
  data?: {
    taskId: string;
    status: TaskStatus;
  };
}

export interface RemoveTaskResponse {
  status: 'success' | 'error';
  message: string;
}

export interface EventWithTasks {
  id: string;
  title: string;
  eventType: string;
  status: string;
  tasks: Task[];
  createdAt: string;
}
