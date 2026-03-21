import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { EventTasksConfirmResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: {
    eventId: string;
  };
};

export async function POST(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<EventTasksConfirmResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${params.eventId}/tasks/confirm`) as Promise<NextResponse<EventTasksConfirmResponse>>;
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
    const result = eventStore.confirmTasks(eventId);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Tasks confirmed and event updated successfully.',
        data: result,
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to confirm tasks.';

    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 400 }
    );
  }
}
