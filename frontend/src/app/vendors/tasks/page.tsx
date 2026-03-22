'use client';

import { VendorTasksDashboard } from '@/components/vendor/VendorTasksDashboard';

export default function VendorTasksPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto">
        <VendorTasksDashboard />
      </div>
    </div>
  );
}
