'use client';

import { useState } from 'react';
import { VendorTasksDashboard } from '@/components/vendor/VendorTasksDashboard';
import { VendorTaskDetail } from '@/components/vendor/VendorTaskDetail';

export default function VendorTasksPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);

  if (selectedTaskId) {
    return (
      <VendorTaskDetail
        taskId={selectedTaskId}
        onBack={() => setSelectedTaskId(null)}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <VendorTasksDashboard onTaskSelect={setSelectedTaskId} />
      </div>
    </div>
  );
}
