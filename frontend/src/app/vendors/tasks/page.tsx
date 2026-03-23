'use client';

import VendorPortalShell from '@/components/features/vendor/VendorPortalShell';
import { VendorTasksDashboard } from '@/components/vendor/VendorTasksDashboard';

export default function VendorTasksPage() {
  return (
    <VendorPortalShell>
      <div className="max-w-7xl mx-auto">
        <VendorTasksDashboard />
      </div>
    </VendorPortalShell>
  );
}
