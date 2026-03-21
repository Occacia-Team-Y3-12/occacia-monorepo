import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { DeleteDraftEventResponse } from '@/types/customer';
import { EventDetailResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: {
    eventId: string;
  };
};

export async function GET(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<EventDetailResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${params.eventId}`) as Promise<NextResponse<EventDetailResponse>>;
  }

  try {
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

    const record = eventStore.ensureEvent(eventId);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Event fetched successfully.',
        data: {
          event: record.event,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to fetch event.';
    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<DeleteDraftEventResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${params.eventId}`) as Promise<NextResponse<DeleteDraftEventResponse>>;
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

  const deleted = eventStore.deleteDraft(eventId);
  if (!deleted) {
    return NextResponse.json(
      {
        status: 'error',
        message: 'Only draft events can be deleted or event was not found.',
      },
      { status: 400 }
    );
  }

  return NextResponse.json(
    {
      status: 'success',
      message: 'Draft deleted successfully.',
    },
    { status: 200 }
  );
}
