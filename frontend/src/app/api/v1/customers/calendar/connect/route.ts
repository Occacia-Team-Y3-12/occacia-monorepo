import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { CalendarConnectRequest, CalendarConnectResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

export async function POST(request: NextRequest): Promise<NextResponse<CalendarConnectResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, '/customers/calendar/connect') as Promise<NextResponse<CalendarConnectResponse>>;
  }

  try {
    const body = (await request.json()) as CalendarConnectRequest;

    if (!body.provider || !['google', 'apple', 'microsoft'].includes(body.provider)) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'A valid calendar provider is required.',
        },
        { status: 400 }
      );
    }

    const status = eventStore.connectCalendar(body.provider);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Calendar connected successfully.',
        data: {
          status,
        },
      },
      { status: 200 }
    );
  } catch {
    return NextResponse.json(
      {
        status: 'error',
        message: 'Failed to connect calendar provider.',
      },
      { status: 400 }
    );
  }
}
