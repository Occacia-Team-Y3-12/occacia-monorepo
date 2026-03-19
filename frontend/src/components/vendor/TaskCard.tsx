'use client';

import { TaskListItem, TaskPriority, TaskStatus } from '@/types/vendorTasks';
import { 
  Clock, 
  Calendar, 
  User, 
  AlertTriangle,
  ChevronRight,
  DollarSign
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';

interface TaskCardProps {
  task: TaskListItem;
  onClick: () => void;
}

const statusConfig: Record<TaskStatus, { label: string; color: string; icon: typeof Clock }> = {
  pending_response: {
    label: 'Pending Response',
    color: 'bg-amber-100 text-amber-800 border-amber-200',
    icon: Clock,
  },
  assigned: {
    label: 'In Progress',
    color: 'bg-blue-100 text-blue-800 border-blue-200',
    icon: Calendar,
  },
  completed: {
    label: 'Completed',
    color: 'bg-green-100 text-green-800 border-green-200',
    icon: ChevronRight,
  },
  rejected: {
    label: 'Rejected',
    color: 'bg-red-100 text-red-800 border-red-200',
    icon: AlertTriangle,
  },
  expired: {
    label: 'Expired',
    color: 'bg-gray-100 text-gray-800 border-gray-200',
    icon: Clock,
  },
};

const priorityConfig: Record<TaskPriority, string> = {
  high: 'text-red-600 bg-red-50',
  medium: 'text-orange-600 bg-orange-50',
  low: 'text-green-600 bg-green-50',
};

export function TaskCard({ task, onClick }: TaskCardProps) {
  const status = statusConfig[task.status];
  const StatusIcon = status.icon;

  return (
    <div 
      onClick={onClick}
      className={`
        group relative bg-white rounded-xl border-2 border-gray-100 p-6 
        hover:border-blue-300 hover:shadow-lg transition-all duration-200 
        cursor-pointer
        ${task.is_urgent ? 'border-l-4 border-l-red-500' : ''}
      `}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${status.color}`}>
              <StatusIcon className="w-3.5 h-3.5" />
              {status.label}
            </span>
            {task.is_urgent && (
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                <AlertTriangle className="w-3 h-3" />
                Urgent
              </span>
            )}
            <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${priorityConfig[task.priority]}`}>
              {task.priority}
            </span>
          </div>

          <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
            {task.title}
          </h3>
          
          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mt-3">
            <div className="flex items-center gap-1.5">
              <User className="w-4 h-4 text-gray-400" />
              <span className="font-medium">{task.customer.name}</span>
            </div>
            
            {task.event && (
              <div className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-gray-400" />
                <span>{task.event.occasion_type}</span>
                {task.event.event_date && (
                  <span className="text-gray-500">
                    ({format(new Date(task.event.event_date), 'MMM d, yyyy')})
                  </span>
                )}
              </div>
            )}

            {task.budget_range && (
              <div className="flex items-center gap-1.5">
                <DollarSign className="w-4 h-4 text-gray-400" />
                <span>{task.budget_range}</span>
              </div>
            )}

            {task.due_date && (
              <div className={`flex items-center gap-1.5 ${task.is_urgent ? 'text-red-600 font-medium' : ''}`}>
                <Clock className="w-4 h-4" />
                <span>
                  Due {formatDistanceToNow(new Date(task.due_date), { addSuffix: true })}
                </span>
              </div>
            )}
          </div>
        </div>

        <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all flex-shrink-0" />
      </div>
    </div>
  );
}