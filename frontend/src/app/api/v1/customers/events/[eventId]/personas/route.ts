import { NextRequest, NextResponse } from 'next/server';
import { UpdateEventPersonasPayload, UpdateEventPersonasResponse } from '@/types/customer';

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

    return NextResponse.json(
      {
        status: 'success',
        message: 'Personas updated successfully.',
        data: {
          eventId: params.eventId,
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
