'use client';

import { Inbox, Search, CheckCircle } from 'lucide-react';
import { TaskStatus } from '@/types/vendorTasks';

interface EmptyStateProps {
  status: TaskStatus;
  onClearFilters: () => void;
}

const emptyStateConfig: Record<TaskStatus, { icon: typeof Inbox; title: string; description: string }> = {
  pending_response: {
    icon: Inbox,
    title: 'No pending requests',
    description: 'You have no new task requests requiring your response. Check back later!',
  },
  assigned: {
    icon: CheckCircle,
    title: 'No active tasks',
    description: 'You currently have no tasks in progress. Accept pending requests to get started.',
  },
  completed: {
    icon: CheckCircle,
    title: 'No completed tasks yet',
    description: 'Your completed tasks will appear here.',
  },
  rejected: {
    icon: Inbox,
    title: 'No rejected or expired tasks',
    description: 'Tasks you reject or fail to respond to in time will appear here.',
  },
  expired: {
    icon: Inbox,
    title: 'No expired tasks',
    description: 'Tasks you fail to respond to in time will appear here.',
  },
};

export function EmptyState({ status, onClearFilters }: EmptyStateProps) {
  const config = emptyStateConfig[status] || emptyStateConfig.pending_response;
  const Icon = config.icon;

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
      <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{config.title}</h3>
      <p className="text-gray-500 max-w-sm mb-6">{config.description}</p>
      <button
        onClick={onClearFilters}
        className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium"
      >
        <Search className="w-4 h-4" />
        Clear filters
      </button>
    </div>
  );
}