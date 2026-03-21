'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useEventTasks } from '@/hooks/customer/useEventTasks';
import { Task, TaskDetails, TaskStatus } from '@/types/customer/task';
import ModifyTaskModal from '@/components/customer/ModifyTaskModal';
import Button from '@/components/ui/Button';

const statusColors: Record<TaskStatus, string> = {
  Pending: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  Assigned: 'bg-blue-100 text-blue-800 border-blue-300',
  'In Progress': 'bg-purple-100 text-purple-800 border-purple-300',
  Rejected: 'bg-red-100 text-red-800 border-red-300',
  Done: 'bg-green-100 text-green-800 border-green-300',
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
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading event tasks...</p>
        </div>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Event not found'}</p>
          <Button onClick={() => router.push('/customer/events')}>Back to Events</Button>
        </div>
      </div>
    );
  }



  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <Button variant="ghost" onClick={() => router.push('/customer/events')}>
            ← Back to Events
          </Button>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{event.title}</h1>
          <p className="text-gray-600">Event Type: {event.eventType}</p>
          {rejectedCount > 0 && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 font-medium">
                ⚠️ {rejectedCount} task{rejectedCount > 1 ? 's' : ''} rejected. Click to modify.
              </p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Task Status</h2>
          
          {event.tasks.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No tasks found for this event.</p>
          ) : (
            <div className="space-y-3">
              {event.tasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => handleTaskClick(task)}
                  className={`border rounded-lg p-4 transition ${
                    task.status === 'Rejected'
                      ? 'cursor-pointer hover:shadow-md'
                      : 'cursor-default'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{task.serviceType}</h3>
                      <p className="text-sm text-gray-600 mt-1">Vendor: {task.vendorName}</p>
                      <p className="text-sm text-gray-500">${task.price}</p>
                    </div>
                    <div>
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-medium border ${
                          statusColors[task.status]
                        }`}
                      >
                        {task.status}
                      </span>
                    </div>
                  </div>
                  {task.status === 'Rejected' && task.rejectionReason && (
                    <p className="text-sm text-red-600 mt-2">
                      Reason: {task.rejectionReason}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
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
