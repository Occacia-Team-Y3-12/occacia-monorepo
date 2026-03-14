import { NextResponse } from 'next/server';
import { EventMessagesResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: {
    eventId: string;
  };
};

export async function GET(
  _request: Request,
  { params }: RouteContext
): Promise<NextResponse<EventMessagesResponse>> {
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
