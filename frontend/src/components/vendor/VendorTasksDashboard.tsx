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
  return `${task.vendorCategory ?? 'General'} - ${budget}`;
}

function requestLabel(request: FulfillmentRequestItem): string {
  return `Task ${request.taskId} - Attempt ${request.attemptNo}`;
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

  const tableRows = useMemo(
    () => [
      ...pendingRequests.map((request) => ({ type: 'request' as const, request })),
      ...assignedTasks.map((task) => ({ type: 'task' as const, task, lane: 'ASSIGNED' as const })),
      ...inProgressTasks.map((task) => ({ type: 'task' as const, task, lane: 'IN_PROGRESS' as const })),
      ...doneTasks.map((task) => ({ type: 'task' as const, task, lane: 'DONE' as const })),
    ],
    [pendingRequests, assignedTasks, inProgressTasks, doneTasks]
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
    <div className="space-y-5">
      <div className="rounded-2xl border border-[#E2E5EC] bg-white px-4 py-5 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:px-6">
        <h1 className="text-3xl font-bold text-[#1F293F]">Vendor Task Board</h1>
        <p className="mt-1 text-sm text-[#5B6478]">
          {totalTasks} total items | Requests: {pendingRequests.length} | Assigned: {assignedTasks.length} | In Progress: {inProgressTasks.length} | Done: {doneTasks.length}
        </p>
      </div>

      <section className="rounded-2xl border border-[#E2E5EC] bg-white p-4 shadow-[0_4px_16px_rgba(15,23,42,0.06)] sm:p-5">
        {tableRows.length === 0 ? (
          <Card>
            <CardBody>
              <p className="text-gray-600">No tasks or requests available right now.</p>
            </CardBody>
          </Card>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1020px] border-separate border-spacing-y-2">
              <thead>
                <tr className="text-left text-[12px] font-semibold uppercase tracking-wide text-slate-400">
                  <th className="px-2 py-1">Type</th>
                  <th className="px-2 py-1">Title</th>
                  <th className="px-2 py-1">Details</th>
                  <th className="px-2 py-1">Status</th>
                  <th className="px-2 py-1">Countdown</th>
                  <th className="px-2 py-1">Actions</th>
                </tr>
              </thead>
              <tbody>
                {tableRows.map((row) => {
                  if (row.type === 'request') {
                    const { request } = row;
                    const busy = actionLoading[`request:${request.fulfillmentRequestId}`] ?? false;
                    const expired = isExpired(request.respondBy, nowMs);
                    const remainingMs = request.respondBy
                      ? new Date(request.respondBy).getTime() - nowMs
                      : Number.POSITIVE_INFINITY;

                    return (
                      <tr key={`request-${request.fulfillmentRequestId}`} className="rounded-xl bg-amber-50/60">
                        <td className="rounded-l-xl px-2 py-3">
                          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                            Request
                          </span>
                        </td>
                        <td className="px-2 py-3 text-sm font-semibold text-slate-800">{requestLabel(request)}</td>
                        <td className="px-2 py-3 text-sm text-slate-600">Task ID: {request.taskId}</td>
                        <td className="px-2 py-3">
                          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${expired ? 'bg-rose-100 text-rose-700' : 'bg-blue-100 text-blue-700'}`}>
                            {expired ? 'Expired' : 'Pending Response'}
                          </span>
                        </td>
                        <td className="px-2 py-3 text-sm text-slate-700">{formatCountdown(remainingMs)}</td>
                        <td className="rounded-r-xl px-2 py-3">
                          <div className="flex items-center gap-2">
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
                        </td>
                      </tr>
                    );
                  }

                  const { task, lane } = row;
                  const busy = actionLoading[`task:${task.taskId}`] ?? false;
                  const laneStyle =
                    lane === 'ASSIGNED'
                      ? 'bg-blue-100 text-blue-700'
                      : lane === 'IN_PROGRESS'
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'bg-emerald-100 text-emerald-700';

                  return (
                    <tr key={`task-${task.taskId}`} className="rounded-xl bg-slate-50">
                      <td className="rounded-l-xl px-2 py-3">
                        <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-700">
                          Task
                        </span>
                      </td>
                      <td className="px-2 py-3 text-sm font-semibold text-slate-800">{task.name}</td>
                      <td className="px-2 py-3 text-xs text-slate-600">{taskMeta(task)}</td>
                      <td className="px-2 py-3">
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${laneStyle}`}>
                          {lane === 'ASSIGNED' ? 'Assigned' : lane === 'IN_PROGRESS' ? 'In Progress' : 'Done'}
                        </span>
                      </td>
                      <td className="px-2 py-3 text-sm text-slate-600">
                        {lane === 'DONE' ? (
                          <span className="inline-flex items-center gap-1 text-emerald-700">
                            <Clock3 className="h-3.5 w-3.5" />
                            Completed
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="rounded-r-xl px-2 py-3">
                        {lane === 'ASSIGNED' ? (
                          <Button
                            size="sm"
                            disabled={busy}
                            onClick={() => handleTaskTransition(task, 'IN_PROGRESS')}
                          >
                            <PlayCircle className="h-4 w-4" />
                            Start Task
                          </Button>
                        ) : lane === 'IN_PROGRESS' ? (
                          <Button
                            size="sm"
                            className="bg-emerald-600 hover:bg-emerald-700"
                            disabled={busy}
                            onClick={() => handleTaskTransition(task, 'DONE')}
                          >
                            <CheckCircle2 className="h-4 w-4" />
                            Mark Done
                          </Button>
                        ) : (
                          <span className="text-xs font-semibold text-emerald-700">No action</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
