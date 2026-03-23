'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import VendorPortalShell from '@/components/features/vendor/VendorPortalShell';
import { vendorTaskApi } from '@/services/vendorTaskApi';
import { TaskCard } from '@/components/vendor/TaskCard';
import { TaskStatusTabs } from '@/components/vendor/TaskStatusTabs';
import { TaskFilters } from '@/components/vendor/TaskFilters';
import { EmptyState } from '@/components/vendor/EmptyState';
import { LoadingSkeleton } from '@/components/vendor/LoadingSkeleton';
import { TaskStatus, TaskListItem, TaskPriority } from '@/types/vendorTasks';
import { AlertCircle } from 'lucide-react';

export default function VendorActivitiesPage() {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <VendorActivitiesContent />
    </QueryClientProvider>
  );
}

function VendorActivitiesContent() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TaskStatus>('pending_response');
  const [filters, setFilters] = useState<{ search?: string; priority?: TaskPriority }>({
    search: undefined,
    priority: undefined,
  });

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['vendor-tasks', activeTab, filters],
    queryFn: () => vendorTaskApi.getTasks(filters),
    staleTime: 30000, // 30 seconds
  });

  const getTasksForTab = () => {
    if (!data) return [];
    switch (activeTab) {
      case 'pending_response': return data.pending_response;
      case 'assigned': return data.assigned;
      case 'completed': return data.completed;
      case 'rejected':
      case 'expired': return data.rejected_expired;
      default: return [];
    }
  };

  const tasks = getTasksForTab();
  const counts = {
    pending_response: data?.pending_response.length || 0,
    assigned: data?.assigned.length || 0,
    completed: data?.completed.length || 0,
    rejected_expired: data?.rejected_expired.length || 0,
  };

  if (isLoading) return <LoadingSkeleton />;
  
  if (error) {
    return (
      <VendorPortalShell>
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4 rounded-2xl border border-slate-200 bg-white">
          <AlertCircle className="w-12 h-12 text-red-500" />
          <h3 className="text-lg font-semibold">Failed to load activities</h3>
          <button 
            onClick={() => refetch()}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
          >
            Try Again
          </button>
        </div>
      </VendorPortalShell>
    );
  }

  return (
    <VendorPortalShell>
    <div className="container mx-auto px-0 py-2 max-w-7xl">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Assigned Activities</h1>
          <p className="text-gray-600 mt-1">
            Manage your event tasks and customer requests
          </p>
        </div>
        <div className="flex items-center gap-2 bg-blue-50 px-4 py-2 rounded-full">
          <span className="text-blue-700 font-medium">
            {data?.total_count || 0} Total Tasks
          </span>
        </div>
      </div>

      <TaskFilters filters={filters} onChange={setFilters} />

      <TaskStatusTabs 
        activeTab={activeTab} 
        onChange={setActiveTab}
        counts={counts}
      />

      <div className="mt-6">
        {tasks.length === 0 ? (
          <EmptyState 
            status={activeTab} 
            onClearFilters={() => setFilters({ search: '', priority: undefined })}
          />
        ) : (
          <div className="grid gap-4">
            {tasks.map((task: TaskListItem) => (
              <TaskCard 
                key={task.id} 
                task={task}
                onClick={() => router.push(`/vendor/activities/${task.id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
    </VendorPortalShell>
  );
}
