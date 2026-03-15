import { NextRequest, NextResponse } from 'next/server';
import { UpdateEventPersonasPayload, UpdateEventPersonasResponse } from '@/types/customer';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: {
    eventId: string;
  };
};

export async function PUT(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<UpdateEventPersonasResponse>> {
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

    const body = (await request.json()) as UpdateEventPersonasPayload;

    if (!Array.isArray(body.personaIds)) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'personaIds must be an array.',
        },
        { status: 400 }
      );
    }

    eventStore.updatePersonas(eventId, body.personaIds);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Personas updated successfully.',
        data: {
          eventId,
          personaIds: body.personaIds,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Update personas error:', error);
    return NextResponse.json(
      {
        status: 'error',
        message: 'Failed to update personas.',
      },
      { status: 500 }
    );
  }
}
