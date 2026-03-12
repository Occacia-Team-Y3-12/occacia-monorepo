import { NextResponse } from 'next/server';
import { DeleteDraftEventResponse } from '@/types/customer';

type RouteContext = {
  params: {
    eventId: string;
  };
};

export async function DELETE(
  _request: Request,
  { params }: RouteContext
): Promise<NextResponse<DeleteDraftEventResponse>> {
  if (!params.eventId) {
    return NextResponse.json(
      {
        status: 'error',
        message: 'Event id is required.',
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
