import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { CalendarStatusResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

export async function GET(request: NextRequest): Promise<NextResponse<CalendarStatusResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, '/customers/calendar/status') as Promise<NextResponse<CalendarStatusResponse>>;
  }

  const status = eventStore.getCalendarStatus();

  return NextResponse.json(
    {
      status: 'success',
      message: 'Calendar connection status fetched successfully.',
      data: {
        status,
      },
    },
    { status: 200 }
  );
}
