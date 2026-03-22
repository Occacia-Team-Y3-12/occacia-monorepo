'use client';

import { useState, useEffect } from 'react';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { AlertCircle, CheckCircle2, Clock, XCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface TaskListItem {
  id: number;
  title: string;
  status: 'pending_response' | 'assigned' | 'completed' | 'rejected' | 'expired';
  priority: 'high' | 'medium' | 'low';
  due_date: string | null;
  expiry_date: string | null;
  budget_range: string | null;
  customer: { id: number; name: string; email: string };
  event: { id: number; title: string; occasion_type: string; event_date: string } | null;
  created_at: string;
  is_urgent: boolean;
}

interface TaskListResponse {
  pending_response: TaskListItem[];
  assigned: TaskListItem[];
  completed: TaskListItem[];
  rejected_expired: TaskListItem[];
  total_count: number;
}

type TaskSectionStatus = 'pending_response' | 'assigned' | 'completed' | 'rejected_expired';

const statusConfig = {
  pending_response: {
    label: 'Needs Response',
    icon: AlertCircle,
    color: 'bg-amber-100 text-amber-800',
    badgeColor: 'bg-amber-200',
  },
  assigned: {
    label: 'In Progress',
    icon: Clock,
    color: 'bg-blue-100 text-blue-800',
    badgeColor: 'bg-blue-200',
  },
  completed: {
    label: 'Completed',
    icon: CheckCircle2,
    color: 'bg-green-100 text-green-800',
    badgeColor: 'bg-green-200',
  },
  rejected_expired: {
    label: 'Rejected/Expired',
    icon: XCircle,
    color: 'bg-red-100 text-red-800',
    badgeColor: 'bg-red-200',
  },
};

const priorityConfig = {
  high: { label: 'High', color: 'bg-red-100 text-red-700' },
  medium: { label: 'Medium', color: 'bg-yellow-100 text-yellow-700' },
  low: { label: 'Low', color: 'bg-green-100 text-green-700' },
};

const badgeClass = 'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold';

const getTaskStatusConfig = (status: TaskListItem['status']) => {
  if (status === 'rejected' || status === 'expired') {
    return statusConfig.rejected_expired;
  }
  return statusConfig[status];
};

interface TaskCardProps {
  task: TaskListItem;
  onViewDetail: (taskId: number) => void;
}

const TaskCard: React.FC<TaskCardProps> = ({ task, onViewDetail }) => {
  const config = getTaskStatusConfig(task.status);
  const Icon = config.icon;

  return (
    <Card className={`${config.color} border-none cursor-pointer hover:shadow-lg transition-shadow`}>
      <CardBody className="pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Icon className="h-5 w-5" />
              <h3 className="font-semibold text-lg">{task.title}</h3>
              {task.is_urgent && <span className={`${badgeClass} bg-red-500 text-white`}>Urgent</span>}
            </div>

            <div className="space-y-2 text-sm">
              <p>
                <span className="font-medium">Customer:</span> {task.customer.name}
              </p>
              {task.event && (
                <p>
                  <span className="font-medium">Event:</span> {task.event.title} ({task.event.occasion_type})
                </p>
              )}
              {task.budget_range && (
                <p>
                  <span className="font-medium">Budget:</span> {task.budget_range}
                </p>
              )}
              {task.due_date && (
                <p>
                  <span className="font-medium">Due:</span> {formatDistanceToNow(new Date(task.due_date), { addSuffix: true })}
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-2 items-end">
            <span className={`${badgeClass} ${priorityConfig[task.priority].color}`}>
              {priorityConfig[task.priority].label}
            </span>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => onViewDetail(task.id)}
              className="mt-2"
            >
              View Details
            </Button>
          </div>
        </div>
      </CardBody>
    </Card>
  );
};

interface TaskSectionProps {
  title: string;
  tasks: TaskListItem[];
  status: TaskSectionStatus;
  onViewDetail: (taskId: number) => void;
}

const TaskSection: React.FC<TaskSectionProps> = ({ title, tasks, status, onViewDetail }) => {
  const config = statusConfig[status];

  if (tasks.length === 0) {
    return (
      <Card>
        <CardHeader>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <config.icon className="h-5 w-5" />
            {title}
          </h2>
          <p className="text-sm text-gray-600">No tasks in this category</p>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <config.icon className="h-6 w-6" />
        {title}
        <span className={`${badgeClass} bg-gray-200 text-gray-700`}>{tasks.length}</span>
      </h2>
      <div className="space-y-4">
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} onViewDetail={onViewDetail} />
        ))}
      </div>
    </div>
  );
};

interface VendorTasksDashboardProps {
  onTaskSelect?: (taskId: number) => void;
}

export function VendorTasksDashboard({ onTaskSelect }: VendorTasksDashboardProps) {
  const [tasks, setTasks] = useState<TaskListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/vendors/tasks', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to load tasks');

      const data: TaskListResponse = await response.json();
      setTasks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = (taskId: number) => {
    // Navigate to task detail or call callback
    if (onTaskSelect) {
      onTaskSelect(taskId);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p>Loading tasks...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <h2 className="text-xl font-semibold text-red-700">Error Loading Tasks</h2>
        </CardHeader>
        <CardBody>
          <p className="text-red-600">{error}</p>
          <Button onClick={fetchTasks} className="mt-4">
            Retry
          </Button>
        </CardBody>
      </Card>
    );
  }

  if (!tasks) return null;

  return (
    <div className="space-y-8 p-6">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Your Tasks</h1>
        <p className="text-gray-600">
          Total: <span className="font-semibold">{tasks.total_count}</span> tasks
        </p>
      </div>

      {/* Needs Response Section */}
      <TaskSection
        title="Actions Required"
        tasks={tasks.pending_response}
        status="pending_response"
        onViewDetail={handleViewDetail}
      />

      {/* In Progress Section */}
      <TaskSection
        title="In Progress"
        tasks={tasks.assigned}
        status="assigned"
        onViewDetail={handleViewDetail}
      />

      {/* Completed Section */}
      <TaskSection
        title="Completed"
        tasks={tasks.completed}
        status="completed"
        onViewDetail={handleViewDetail}
      />

      {/* Rejected/Expired Section */}
      <TaskSection
        title="Rejected & Expired"
        tasks={tasks.rejected_expired}
        status="rejected_expired"
        onViewDetail={handleViewDetail}
      />
    </div>
  );
}
