import { NextRequest, NextResponse } from 'next/server';
import { CreateCustomerEventPayload, CreateCustomerEventResponse } from '@/types/customer';

export async function POST(request: NextRequest): Promise<NextResponse<CreateCustomerEventResponse>> {
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

    await new Promise((resolve) => setTimeout(resolve, 450));

    const eventId = `evt_${Date.now()}`;

    return NextResponse.json(
      {
        status: 'success',
        message: 'Event draft created successfully.',
        data: {
          eventId,
          state: 'draft',
        },
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Create event error:', error);
    return NextResponse.json(
      {
        status: 'error',
        message: 'Failed to create event.',
      },
      { status: 500 }
    );
  }
}
