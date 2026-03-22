import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import {
  CreateCustomerEventPayload,
  CreateCustomerEventResponse,
  PaginatedCustomerEventsResponse,
} from '@/types/customer';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

export async function GET(request: NextRequest): Promise<NextResponse<PaginatedCustomerEventsResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, '/customers/events') as Promise<NextResponse<PaginatedCustomerEventsResponse>>;
  }

  const { searchParams } = new URL(request.url);
  const limit = Number.parseInt(searchParams.get('limit') || '20', 10);

  return NextResponse.json(
    eventStore.listEvents({
      status: searchParams.get('status'),
      limit: Number.isNaN(limit) ? 20 : limit,
      cursor: searchParams.get('cursor'),
    }),
    { status: 200 }
  );
}

export async function POST(request: NextRequest): Promise<NextResponse<CreateCustomerEventResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, '/customers/events') as Promise<NextResponse<CreateCustomerEventResponse>>;
  }

  try {
    const body = (await request.json()) as CreateCustomerEventPayload;

    if (!body.eventType || !['individual', 'group', 'others'].includes(body.eventType)) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Invalid event type.',
        },
        { status: 400 }
      );
    }

    const title = body.title?.trim() || '';
    if (title.length < 3) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Event title must be at least 3 characters.',
        },
        { status: 400 }
      );
    }

    await new Promise((resolve) => setTimeout(resolve, 250));
    const event = eventStore.createEvent(body);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Event draft created successfully.',
        data: {
          eventId: event.eventId,
          state: 'draft',
        },
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Create event error:', error);
    const message = error instanceof Error ? error.message : 'Failed to create event.';
    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 500 }
    );
  }
}
