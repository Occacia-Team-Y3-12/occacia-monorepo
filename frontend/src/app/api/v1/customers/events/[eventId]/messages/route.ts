import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { EventMessagesResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: {
    eventId: string;
  };
};

export async function GET(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<EventMessagesResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${params.eventId}/messages`) as Promise<NextResponse<EventMessagesResponse>>;
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
    const messages = eventStore.getMessages(eventId);
    return NextResponse.json(
      {
        status: 'success',
        message: 'Messages fetched successfully.',
        data: {
          messages,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to fetch messages.';
    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 404 }
    );
  }
}
