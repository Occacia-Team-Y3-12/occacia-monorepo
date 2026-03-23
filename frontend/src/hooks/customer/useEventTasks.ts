import { useState, useEffect } from 'react';
import { taskService } from '@/services/customer/taskService';
import { EventWithTasks, TaskDetails } from '@/types/customer/task';

export const useEventTasks = (eventId: string) => {
  const [event, setEvent] = useState<EventWithTasks | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTasks = async () => {
    setIsLoading(true);
    setError(null);
    const result = await taskService.getEventWithTasks(eventId);
    
    if (result.ok && result.data) {
      setEvent(result.data);
    } else {
      setError(result.error || 'Failed to load tasks');
    }
    setIsLoading(false);
  };

  const getTaskDetails = async (taskId: string): Promise<TaskDetails | null> => {
    const result = await taskService.getTaskDetails(eventId, taskId);
    return result.ok && result.data ? result.data : null;
  };

  const reassignTask = async (taskId: string, newVendorId: string): Promise<boolean> => {
    const result = await taskService.reassignTask(eventId, taskId, { newVendorId });
    if (result.ok) {
      await loadTasks();
      return true;
    }
    setError(result.error || 'Failed to reassign task');
    return false;
  };

  const removeTask = async (taskId: string): Promise<boolean> => {
    const result = await taskService.removeTask(eventId, taskId);
    if (result.ok) {
      await loadTasks();
      return true;
    }
    setError(result.error || 'Failed to remove task');
    return false;
  };

  useEffect(() => {
    if (eventId) loadTasks();
  }, [eventId]);

  return {
    event,
    isLoading,
    error,
    loadTasks,
    getTaskDetails,
    reassignTask,
    removeTask,
    rejectedCount: Array.isArray(event?.tasks)
      ? event.tasks.filter((t) => t.status === 'Rejected').length
      : 0,
  };
};
