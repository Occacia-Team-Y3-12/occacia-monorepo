'use client';

import { useState, useEffect } from 'react';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { ArrowLeft, Mail, Clock, CheckCircle, XCircle } from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';

interface TaskDetail {
  id: number;
  title: string;
  description: string | null;
  status: 'pending_response' | 'assigned' | 'completed' | 'rejected' | 'expired';
  priority: 'high' | 'medium' | 'low';
  budget_min: number | null;
  budget_max: number | null;
  agreed_price: number | null;
  due_date: string | null;
  expiry_date: string | null;
  completed_at: string | null;
  responded_at: string | null;
  created_at: string;
  customer: { id: number; name: string; email: string };
  event: {
    id: number;
    title: string;
    occasion_type: string;
    event_date: string;
  } | null;
  offering: { id: number; name: string; category: string } | null;
  time_remaining: string | null;
  can_respond: boolean;
}

interface TaskDetailProps {
  taskId: number;
  onBack?: () => void;
}

const StatusBadges = {
  pending_response: { label: 'Needs Response', bg: 'bg-amber-100', text: 'text-amber-800' },
  assigned: { label: 'In Progress', bg: 'bg-blue-100', text: 'text-blue-800' },
  completed: { label: 'Completed', bg: 'bg-green-100', text: 'text-green-800' },
  rejected: { label: 'Rejected', bg: 'bg-red-100', text: 'text-red-800' },
  expired: { label: 'Expired', bg: 'bg-gray-100', text: 'text-gray-800' },
};

const PriorityBadges = {
  high: { label: 'High', bg: 'bg-red-100', text: 'text-red-700' },
  medium: { label: 'Medium', bg: 'bg-yellow-100', text: 'text-yellow-700' },
  low: { label: 'Low', bg: 'bg-green-100', text: 'text-green-700' },
};

const pillClass = 'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold';

export function VendorTaskDetail({ taskId, onBack }: TaskDetailProps) {
  const [task, setTask] = useState<TaskDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [responding, setResponding] = useState(false);

  useEffect(() => {
    fetchTaskDetail();
  }, [taskId]);

  const fetchTaskDetail = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/vendors/tasks/${taskId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) throw new Error('Failed to load task details');

      const data: TaskDetail = await response.json();
      setTask(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async () => {
    try {
      setResponding(true);
      // TODO: Implement accept response API
      console.log('Accept task:', taskId);
    } finally {
      setResponding(false);
    }
  };

  const handleReject = async () => {
    try {
      setResponding(true);
      // TODO: Implement reject response API
      console.log('Reject task:', taskId);
    } finally {
      setResponding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <p>Loading task details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <h2 className="text-xl font-semibold text-red-700">Error Loading Task</h2>
        </CardHeader>
        <CardBody>
          <p className="text-red-600">{error}</p>
          <Button onClick={fetchTaskDetail} className="mt-4">
            Retry
          </Button>
        </CardBody>
      </Card>
    );
  }

  if (!task) return null;

  const status = StatusBadges[task.status as keyof typeof StatusBadges];
  const priority = PriorityBadges[task.priority as keyof typeof PriorityBadges];

  return (
    <div className="space-y-6 p-6">
      {/* Header with back button */}
      <div className="flex items-center gap-4">
        {onBack && (
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        )}
        <h1 className="text-3xl font-bold flex-1">{task.title}</h1>
      </div>

      {/* Status and Priority */}
      <div className="flex gap-2">
        <span className={`${pillClass} ${status.bg} ${status.text}`}>{status.label}</span>
        <span className={`${pillClass} ${priority.bg} ${priority.text}`}>{priority.label}</span>
        {task.time_remaining && (
          <span className={`${pillClass} border border-gray-300 text-gray-700`}>{task.time_remaining}</span>
        )}
      </div>

      {/* Main content grid */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Left column - Task details */}
        <div className="md:col-span-2 space-y-6">
          {/* Description */}
          {task.description && (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold">Description</h2>
              </CardHeader>
              <CardBody>
                <p className="text-gray-700 whitespace-pre-wrap">{task.description}</p>
              </CardBody>
            </Card>
          )}

          {/* Customer Information */}
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold">Customer Information</h2>
            </CardHeader>
            <CardBody className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="font-medium text-lg">{task.customer.name}</div>
              </div>
              <div className="flex items-center gap-3 text-gray-600">
                <Mail className="h-4 w-4" />
                <a href={`mailto:${task.customer.email}`} className="hover:underline">
                  {task.customer.email}
                </a>
              </div>
            </CardBody>
          </Card>

          {/* Event Information */}
          {task.event && (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold">Event Details</h2>
              </CardHeader>
              <CardBody className="space-y-4">
                <div>
                  <p className="text-sm text-gray-500">Event Name</p>
                  <p className="font-semibold text-lg">{task.event.title}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Occasion Type</p>
                  <p className="font-semibold">{task.event.occasion_type}</p>
                </div>
                <div className="flex items-center gap-3 text-gray-600">
                  <Clock className="h-4 w-4" />
                  <span>{format(new Date(task.event.event_date), 'PPP p')}</span>
                </div>
              </CardBody>
            </Card>
          )}
        </div>

        {/* Right column - Sidebar */}
        <div className="space-y-6">
          {/* Timeline */}
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold">Timeline</h2>
            </CardHeader>
            <CardBody className="space-y-4 text-sm">
              <div>
                <p className="text-gray-500">Created</p>
                <p className="font-medium">{format(new Date(task.created_at), 'PPP')}</p>
                <p className="text-gray-400 text-xs">
                  {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                </p>
              </div>

              {task.due_date && (
                <div>
                  <p className="text-gray-500">Due Date</p>
                  <p className="font-medium">{format(new Date(task.due_date), 'PPP')}</p>
                  <p className="text-gray-400 text-xs">
                    {formatDistanceToNow(new Date(task.due_date), { addSuffix: true })}
                  </p>
                </div>
              )}

              {task.expiry_date && (
                <div>
                  <p className="text-gray-500">Response Deadline</p>
                  <p className="font-medium">{format(new Date(task.expiry_date), 'PPP')}</p>
                </div>
              )}

              {task.responded_at && (
                <div>
                  <p className="text-gray-500">Responded</p>
                  <p className="font-medium">{format(new Date(task.responded_at), 'PPP p')}</p>
                </div>
              )}

              {task.completed_at && (
                <div>
                  <p className="text-gray-500">Completed</p>
                  <p className="font-medium">{format(new Date(task.completed_at), 'PPP p')}</p>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Budget Information */}
          <Card>
            <CardHeader>
              <h2 className="text-lg font-semibold">Budget</h2>
            </CardHeader>
            <CardBody className="space-y-3 text-sm">
              {task.budget_min !== null && (
                <div>
                  <p className="text-gray-500">Minimum</p>
                  <p className="font-semibold text-lg">
                    LKR {task.budget_min.toLocaleString()}
                  </p>
                </div>
              )}

              {task.budget_max !== null && (
                <div>
                  <p className="text-gray-500">Maximum</p>
                  <p className="font-semibold text-lg">
                    LKR {task.budget_max.toLocaleString()}
                  </p>
                </div>
              )}

              {task.agreed_price !== null && (
                <div className="border-t pt-3">
                  <p className="text-gray-500">Agreed Price</p>
                  <p className="font-bold text-lg text-green-600">
                    LKR {task.agreed_price.toLocaleString()}
                  </p>
                </div>
              )}
            </CardBody>
          </Card>

          {/* Offering */}
          {task.offering && (
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold">Your Offering</h2>
              </CardHeader>
              <CardBody className="space-y-2">
                <div>
                  <p className="text-gray-500 text-sm">Name</p>
                  <p className="font-semibold">{task.offering.name}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-sm">Category</p>
                  <p className="font-semibold">{task.offering.category}</p>
                </div>
              </CardBody>
            </Card>
          )}

          {/* Actions */}
          {task.can_respond && task.status === 'pending_response' && (
            <Card className="bg-blue-50 border-blue-200">
              <CardHeader>
                <h2 className="text-lg font-semibold">Actions</h2>
                <p className="text-sm text-gray-600">Respond to this task request</p>
              </CardHeader>
              <CardBody className="space-y-3">
                <Button
                  onClick={handleAccept}
                  disabled={responding}
                  className="w-full bg-green-600 hover:bg-green-700"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Accept Task
                </Button>
                <Button
                  onClick={handleReject}
                  disabled={responding}
                  variant="secondary"
                  className="w-full"
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Decline Task
                </Button>
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
