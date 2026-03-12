import { NextResponse } from 'next/server';
import { EventTypesResponse } from '@/types/customer';

export async function GET(): Promise<NextResponse<EventTypesResponse>> {
  return NextResponse.json(
    {
      status: 'success',
      message: 'Event types fetched successfully.',
      data: {
        eventTypes: [
          {
            id: 'individual',
            value: 'individual',
            label: 'Individual',
            example: 'Visit someone',
            titlePlaceholder: 'e.g., Visiting to see sick mom',
          },
          {
            id: 'group',
            value: 'group',
            label: 'Group',
            example: 'Celebration',
            titlePlaceholder: 'e.g., Family dinner planning',
          },
          {
            id: 'others',
            value: 'others',
            label: 'Others',
            example: 'Appointment',
            titlePlaceholder: 'e.g., Doctor appointment this Saturday',
          },
        ],
      },
    },
    { status: 200 }
  );
}
