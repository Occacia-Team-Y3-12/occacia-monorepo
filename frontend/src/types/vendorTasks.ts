// This file contains type definitions for vendor tasks
// The export {} ensures TypeScript recognizes this as a module,
// even though it only contains type exports which are stripped at runtime

export type TaskStatus = 
  | 'pending_response' 
  | 'assigned' 
  | 'completed' 
  | 'rejected' 
  | 'expired';

export type TaskPriority = 'high' | 'medium' | 'low';

export interface CustomerBrief {
  id: number;
  name: string;
  email: string;
}

export interface EventBrief {
  id: number;
  title: string;
  occasion_type: string;
  event_date?: string;
}

export interface TaskListItem {
  id: number;
  title: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string;
  expiry_date?: string;
  budget_range?: string;
  customer: CustomerBrief;
  event?: EventBrief;
  created_at: string;
  is_urgent: boolean;
}

export interface TaskListResponse {
  pending_response: TaskListItem[];
  assigned: TaskListItem[];
  completed: TaskListItem[];
  rejected_expired: TaskListItem[];
  total_count: number;
}

export interface TaskDetail extends TaskListItem {
  description?: string;
  budget_min?: number;
  budget_max?: number;
  agreed_price?: number;
  completed_at?: string;
  responded_at?: string;
  time_remaining?: string;
  can_respond: boolean;
}

// Explicit export to ensure TypeScript recognizes this as a module
export {};