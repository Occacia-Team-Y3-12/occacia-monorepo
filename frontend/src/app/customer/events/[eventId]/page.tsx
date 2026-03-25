'use client';

'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useEventTasks } from '@/hooks/customer/useEventTasks';
import { Task, TaskDetails, TaskStatus } from '@/types/customer/task';
import ModifyTaskModal from '@/components/customer/ModifyTaskModal';
import Button from '@/components/ui/Button';
import { ROUTES } from '@/lib/routes';
import { formatCurrency } from '@/lib/currency';

const statusColors: Record<TaskStatus, string> = {
  Pending: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  Assigned: 'bg-blue-50 text-blue-700 border-blue-200',
  'In Progress': 'bg-purple-50 text-purple-700 border-purple-200',
  Rejected: 'bg-red-50 text-red-700 border-red-200',
  Done: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

export default function EventTrackingPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = params.eventId as string;

  const { event, isLoading, error, getTaskDetails, reassignTask, removeTask, rejectedCount } = useEventTasks(eventId);
  const [selectedTask, setSelectedTask] = useState<TaskDetails | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleTaskClick = async (task: Task) => {
    if (task.status !== 'Rejected') return;
    const taskDetails = await getTaskDetails(task.id);
    if (taskDetails) {
      setSelectedTask(taskDetails);
      setIsModalOpen(true);
    }
  };

  const handleReassign = async (vendorId: string) => {
    if (!selectedTask) return;
    const success = await reassignTask(selectedTask.id, vendorId);
    if (!success) alert('Failed to reassign task');
  };

  const handleRemove = async () => {
    if (!selectedTask) return;
    const success = await removeTask(selectedTask.id);
    if (!success) alert('Failed to remove task');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#f3f5f9]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#0D47A1] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-[#4A5976] text-lg">Loading event tasks...</p>
        </div>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#f3f5f9] px-4">
        <div className="text-center max-w-sm rounded-[22px] border border-red-200 bg-white/70 backdrop-blur px-6 py-5 shadow-lg">
          <p className="text-red-600 mb-4 text-lg font-semibold">{error || 'Event not found'}</p>
          <Button variant="ghost" onClick={() => router.push('/customer/events')}>
            ← Back to Events
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F3F5F9] py-12">
      <div className="mx-auto max-w-5xl px-4 sm:px-6">
        <div className="flex justify-end mb-6">
          <Button variant="ghost" onClick={() => router.push('/customer/events')} className="text-[#0D47A1] border border-[#DCE4F2] bg-white px-4 py-2">
            ← Back to Events
          </Button>
        </div>

        <section className="overflow-hidden rounded-[28px] border border-[#DCE4F2] bg-[linear-gradient(135deg,#0D47A1_0%,#1562CC_48%,#4285F4_100%)] px-6 py-8 text-white shadow-[0_24px_70px_-34px_rgba(13,71,161,0.34)] sm:px-8 sm:py-10">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.28em] text-white/80">Event Overview</p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">{event.title}</h1>
              <p className="mt-2 text-sm text-white/80">Type · {event.eventType}</p>
            </div>
            <div className="inline-flex items-center rounded-[16px] border border-white/30 bg-white/10 px-4 py-2 text-sm font-semibold tracking-tight uppercase text-white/90">
              {event.tasks.length} Tasks
            </div>
          </div>
          {rejectedCount > 0 && (
            <div className="mt-5 rounded-[18px] bg-white/15 p-4 text-sm text-white/80">
              <span className="font-semibold text-white">⚠️ {rejectedCount} rejected task{rejectedCount > 1 ? 's' : ''}</span>
              <p className="mt-1 text-xs">Click a rejected task below to modify the vendor assignment.</p>
            </div>
          )}
        </section>

        <div className="mt-8 flex flex-col gap-6">
          <section className="rounded-[24px] border border-[#DCE4F2] bg-white p-6 shadow-[0_18px_48px_-32px_rgba(13,71,161,0.16)]">
            <h2 className="text-2xl font-semibold text-[#1A2438] mb-4">Task Status Overview</h2>
            {event.tasks.length === 0 ? (
              <p className="text-sm text-[#5B6780] text-center py-10">No tasks created yet. Head to Chat to add planning details.</p>
            ) : (
              <div className="space-y-3">
                {event.tasks.map((task) => (
                  <div
                    key={task.id}
                    onClick={() => handleTaskClick(task)}
                    className={`border ${task.status === 'Rejected' ? 'border-[#FFB4B9]' : 'border-[#E1E6EF]'} rounded-[20px] bg-[#FCFDFF] px-5 py-4 transition ${
                      task.status === 'Rejected' ? 'cursor-pointer hover:shadow-lg' : 'cursor-default'
                    }`}
                  >
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-[#1D273C]">{task.serviceType}</h3>
                        <p className="text-sm text-[#5B6780] mt-1">
                          Vendor: <span className="text-[#0D47A1]">{task.vendorName}</span>
                        </p>
                        <p className="text-sm text-[#7A87A3]">{formatCurrency(task.price)}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(event) => {
                            event.stopPropagation();
                            router.push(ROUTES.CUSTOMER.EVENT_CHAT(eventId));
                          }}
                          className="text-[#0D47A1] border border-[#0D47A1] bg-white px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.2em]"
                        >
                          Edit
                        </Button>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold border ${statusColors[task.status]}`}
                        >
                          {task.status}
                        </span>
                      </div>
                    </div>
                    {task.status === 'Rejected' && task.rejectionReason && (
                      <p className="mt-3 text-sm text-[#D64545]">Reason: {task.rejectionReason}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>

      {selectedTask && (
        <ModifyTaskModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          task={selectedTask}
          onReassign={handleReassign}
          onRemove={handleRemove}
        />
      )}
    </div>
  );
}
