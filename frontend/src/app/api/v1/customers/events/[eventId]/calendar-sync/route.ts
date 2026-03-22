import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { CalendarSyncRequest, CalendarSyncResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: Promise<{
    eventId: string;
  }>;
};

export async function PUT(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<CalendarSyncResponse>> {
  const { eventId } = await params;

  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${eventId}/calendar-sync`) as Promise<NextResponse<CalendarSyncResponse>>;
  }

  if (!eventId) {
    return NextResponse.json(
      {
        status: 'error',
        message: 'Event id is required.',
      },
      { status: 400 }
    );
  }

  try {
    const body = (await request.json()) as CalendarSyncRequest;

    const calendarSync = eventStore.setCalendarSync(eventId, body.enabled, body.provider, body.calendarId);

    return NextResponse.json(
      {
        status: 'success',
        message: body.enabled ? 'Calendar sync enabled successfully.' : 'Calendar sync disabled successfully.',
        data: {
          calendarSync,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to update calendar sync settings.';

    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 400 }
    );
  }
}
