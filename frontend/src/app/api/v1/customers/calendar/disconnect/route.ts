import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

export async function DELETE(request: NextRequest): Promise<NextResponse<{ status: 'success' | 'error'; message: string }>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, '/customers/calendar/disconnect') as Promise<NextResponse<{ status: 'success' | 'error'; message: string }>>;
  }

  eventStore.disconnectCalendar();

  return NextResponse.json(
    {
      status: 'success',
      message: 'Calendar disconnected successfully.',
    },
    { status: 200 }
  );
}
