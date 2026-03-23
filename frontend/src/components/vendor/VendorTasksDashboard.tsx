'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { toast } from 'sonner';
import { CheckCircle2, Clock3, PlayCircle, XCircle } from 'lucide-react';
import {
  vendorTaskApi,
  FulfillmentRequestItem,
  VendorTaskItem,
} from '@/services/vendorTaskApi';

type LoadingMap = Record<string, boolean>;

function formatCountdown(remainingMs: number): string {
  if (remainingMs <= 0) {
    return 'Expired';
  }
  const totalSeconds = Math.floor(remainingMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}h ${String(minutes).padStart(2, '0')}m`;
  }
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function isExpired(respondBy: string | null, nowMs: number): boolean {
  if (!respondBy) {
    return false;
  }
  return new Date(respondBy).getTime() <= nowMs;
}

function partitionTasks(items: VendorTaskItem[]) {
  const assigned: VendorTaskItem[] = [];
  const inProgress: VendorTaskItem[] = [];
  const done: VendorTaskItem[] = [];

  items.forEach((task) => {
    const normalized = String(task.status).toUpperCase();
    if (normalized === 'ASSIGNED') {
      assigned.push(task);
      return;
    }
    if (normalized === 'IN_PROGRESS') {
      inProgress.push(task);
      return;
    }
    if (normalized === 'DONE') {
      done.push(task);
    }
  });

  return { assigned, inProgress, done };
}

function taskMeta(task: VendorTaskItem): string {
  const budget =
    task.budgetMin !== null && task.budgetMax !== null
      ? `Budget: ${task.currency} ${task.budgetMin} - ${task.budgetMax}`
      : 'Budget: N/A';
  return `${task.vendorCategory ?? 'General'} • ${budget}`;
}

function requestLabel(request: FulfillmentRequestItem): string {
  return `Task ${request.taskId} • Attempt ${request.attemptNo}`;
}

export function VendorTasksDashboard() {
  const [pendingRequests, setPendingRequests] = useState<FulfillmentRequestItem[]>([]);
  const [assignedTasks, setAssignedTasks] = useState<VendorTaskItem[]>([]);
  const [inProgressTasks, setInProgressTasks] = useState<VendorTaskItem[]>([]);
  const [doneTasks, setDoneTasks] = useState<VendorTaskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<LoadingMap>({});
  const [nowMs, setNowMs] = useState(Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNowMs(Date.now());
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [requestsResponse, tasksResponse] = await Promise.all([
        vendorTaskApi.getFulfillmentRequests({ status: 'SENT', limit: 100 }),
        vendorTaskApi.getVendorTasks({ limit: 100 }),
      ]);

      setPendingRequests(requestsResponse.items);
      const grouped = partitionTasks(tasksResponse.items);
      setAssignedTasks(grouped.assigned);
      setInProgressTasks(grouped.inProgress);
      setDoneTasks(grouped.done);
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : 'Failed to load vendor dashboard';
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const totalTasks = useMemo(
    () => pendingRequests.length + assignedTasks.length + inProgressTasks.length + doneTasks.length,
    [pendingRequests.length, assignedTasks.length, inProgressTasks.length, doneTasks.length]
  );

  const setBusy = (id: string, value: boolean) => {
    setActionLoading((previous) => ({ ...previous, [id]: value }));
  };

  const handleRespond = async (request: FulfillmentRequestItem, decision: 'ACCEPT' | 'REJECT') => {
    const requestId = request.fulfillmentRequestId;
    if (isExpired(request.respondBy, nowMs)) {
      toast.error('This request is expired and can no longer be updated.');
      return;
    }

    setBusy(`request:${requestId}`, true);
    try {
      const response = await vendorTaskApi.respondToFulfillmentRequest(requestId, { decision });
      setPendingRequests((items) => items.filter((item) => item.fulfillmentRequestId !== requestId));

      if (decision === 'ACCEPT') {
        const normalizedStatus = String(response.task.status).toUpperCase();
        if (normalizedStatus === 'ASSIGNED') {
          setAssignedTasks((items) => [response.task, ...items.filter((item) => item.taskId !== response.task.taskId)]);
        } else if (normalizedStatus === 'IN_PROGRESS') {
          setInProgressTasks((items) => [response.task, ...items.filter((item) => item.taskId !== response.task.taskId)]);
        } else if (normalizedStatus === 'DONE') {
          setDoneTasks((items) => [response.task, ...items.filter((item) => item.taskId !== response.task.taskId)]);
        }
        toast.success('Request accepted. Task moved to your assigned tasks.');
      } else {
        toast.success('Request rejected successfully.');
      }
    } catch (responseError) {
      const message = responseError instanceof Error ? responseError.message : 'Unable to update request';
      toast.error(message);
    } finally {
      setBusy(`request:${requestId}`, false);
    }
  };

  const handleTaskTransition = async (task: VendorTaskItem, nextStatus: 'IN_PROGRESS' | 'DONE') => {
    const taskId = task.taskId;
    const snapshotAssigned = assignedTasks;
    const snapshotInProgress = inProgressTasks;
    const snapshotDone = doneTasks;

    setBusy(`task:${taskId}`, true);
    if (nextStatus === 'IN_PROGRESS') {
      setAssignedTasks((items) => items.filter((item) => item.taskId !== taskId));
      setInProgressTasks((items) => [{ ...task, status: 'IN_PROGRESS' }, ...items]);
    } else {
      setInProgressTasks((items) => items.filter((item) => item.taskId !== taskId));
      setDoneTasks((items) => [{ ...task, status: 'DONE' }, ...items]);
    }

    try {
      const updatedTask = await vendorTaskApi.updateVendorTaskStatus(taskId, { status: nextStatus });
      if (nextStatus === 'IN_PROGRESS') {
        setInProgressTasks((items) =>
          items.map((item) => (item.taskId === taskId ? updatedTask : item))
        );
        toast.success('Task started and moved to In Progress.');
      } else {
        setDoneTasks((items) => items.map((item) => (item.taskId === taskId ? updatedTask : item)));
        toast.success('Task marked as Done.');
      }
    } catch (updateError) {
      setAssignedTasks(snapshotAssigned);
      setInProgressTasks(snapshotInProgress);
      setDoneTasks(snapshotDone);
      const message = updateError instanceof Error ? updateError.message : 'Failed to update task status';
      toast.error(message);
    } finally {
      setBusy(`task:${taskId}`, false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[320px] items-center justify-center">
        <p className="text-gray-600">Loading vendor workboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border border-red-200 bg-red-50">
        <CardHeader>
          <h2 className="text-xl font-semibold text-red-700">Failed to load vendor tasks</h2>
        </CardHeader>
        <CardBody>
          <p className="text-red-600">{error}</p>
          <Button className="mt-4" onClick={loadDashboardData}>
            Retry
          </Button>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="space-y-8 p-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Vendor Task Board</h1>
        <p className="mt-1 text-sm text-gray-600">{totalTasks} total items</p>
      </div>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-gray-900">Requests ({pendingRequests.length})</h2>
        {pendingRequests.length === 0 ? (
          <Card>
            <CardBody>
              <p className="text-gray-600">No pending requests right now.</p>
            </CardBody>
          </Card>
        ) : (
          pendingRequests.map((request) => {
            const expired = isExpired(request.respondBy, nowMs);
            const busy = actionLoading[`request:${request.fulfillmentRequestId}`] ?? false;
            const remainingMs = request.respondBy
              ? new Date(request.respondBy).getTime() - nowMs
              : Number.POSITIVE_INFINITY;

            return (
              <Card key={request.fulfillmentRequestId} className="border border-amber-200 bg-amber-50/50">
                <CardBody className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-amber-900">{requestLabel(request)}</p>
                    <p className="text-xs text-amber-700">
                      Expires in: {formatCountdown(remainingMs)}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                      disabled={busy || expired}
                      onClick={() => handleRespond(request, 'ACCEPT')}
                    >
                      <CheckCircle2 className="h-4 w-4" />
                      Accept
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      disabled={busy || expired}
                      onClick={() => handleRespond(request, 'REJECT')}
                    >
                      <XCircle className="h-4 w-4" />
                      Reject
                    </Button>
                  </div>
                </CardBody>
              </Card>
            );
          })
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-gray-900">Assigned ({assignedTasks.length})</h2>
        {assignedTasks.length === 0 ? (
          <Card>
            <CardBody>
              <p className="text-gray-600">No assigned tasks yet.</p>
            </CardBody>
          </Card>
        ) : (
          assignedTasks.map((task) => {
            const busy = actionLoading[`task:${task.taskId}`] ?? false;
            return (
              <Card key={task.taskId}>
                <CardBody className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="font-semibold text-gray-900">{task.name}</p>
                    <p className="text-xs text-gray-600">{taskMeta(task)}</p>
                  </div>
                  <Button
                    size="sm"
                    disabled={busy}
                    onClick={() => handleTaskTransition(task, 'IN_PROGRESS')}
                  >
                    <PlayCircle className="h-4 w-4" />
                    Start Task
                  </Button>
                </CardBody>
              </Card>
            );
          })
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-gray-900">In Progress ({inProgressTasks.length})</h2>
        {inProgressTasks.length === 0 ? (
          <Card>
            <CardBody>
              <p className="text-gray-600">No tasks in progress.</p>
            </CardBody>
          </Card>
        ) : (
          inProgressTasks.map((task) => {
            const busy = actionLoading[`task:${task.taskId}`] ?? false;
            return (
              <Card key={task.taskId} className="border border-blue-100">
                <CardBody className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="font-semibold text-gray-900">{task.name}</p>
                    <p className="text-xs text-gray-600">{taskMeta(task)}</p>
                  </div>
                  <Button
                    size="sm"
                    className="bg-emerald-600 hover:bg-emerald-700"
                    disabled={busy}
                    onClick={() => handleTaskTransition(task, 'DONE')}
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    Mark Done
                  </Button>
                </CardBody>
              </Card>
            );
          })
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-gray-900">Done ({doneTasks.length})</h2>
        {doneTasks.length === 0 ? (
          <Card>
            <CardBody>
              <p className="text-gray-600">No completed tasks yet.</p>
            </CardBody>
          </Card>
        ) : (
          doneTasks.map((task) => (
            <Card key={task.taskId} className="border border-green-100 bg-green-50/40">
              <CardBody className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-green-900">{task.name}</p>
                  <p className="text-xs text-green-700">{taskMeta(task)}</p>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-700">
                  <Clock3 className="h-3.5 w-3.5" />
                  Completed
                </span>
              </CardBody>
            </Card>
          ))
        )}
      </section>
    </div>
  );
}
