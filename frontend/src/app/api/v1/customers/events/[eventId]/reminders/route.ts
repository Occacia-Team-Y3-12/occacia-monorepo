import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { EventRemindersRequest, EventRemindersResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: {
    eventId: string;
  };
};

export async function PUT(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<EventRemindersResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${params.eventId}/reminders`) as Promise<NextResponse<EventRemindersResponse>>;
  }

  const { eventId } = params;

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
    const body = (await request.json()) as EventRemindersRequest;

    const reminders = eventStore.saveReminders(eventId, {
      enabled: body.enabled,
      channels: body.channels,
      offsetsMinutes: body.offsetsMinutes,
      permissionStatus: body.permissionStatus,
    });

    return NextResponse.json(
      {
        status: 'success',
        message: 'Reminder settings saved successfully.',
        data: {
          reminders,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to save reminders.';

    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 400 }
    );
  }
}
