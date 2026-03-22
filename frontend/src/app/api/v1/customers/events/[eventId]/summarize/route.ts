import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { EventSummaryResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: Promise<{
    eventId: string;
  }>;
};

export async function POST(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<EventSummaryResponse>> {
  const { eventId } = await params;

  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${eventId}/summarize`) as Promise<NextResponse<EventSummaryResponse>>;
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
    const summary = eventStore.summarize(eventId);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Event summary generated successfully.',
        data: {
          summary,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to summarize event.';

    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 404 }
    );
  }
}
