import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { CalendarProvidersResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

export async function GET(request: NextRequest): Promise<NextResponse<CalendarProvidersResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, '/customers/calendar/providers') as Promise<NextResponse<CalendarProvidersResponse>>;
  }

  const providers = eventStore.getCalendarProviders();

  return NextResponse.json(
    {
      status: 'success',
      message: 'Calendar providers fetched successfully.',
      data: {
        providers,
      },
    },
    { status: 200 }
  );
}
