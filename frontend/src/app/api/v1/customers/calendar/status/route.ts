import { NextResponse } from 'next/server';
import { CalendarStatusResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

export async function GET(): Promise<NextResponse<CalendarStatusResponse>> {
  const status = eventStore.getCalendarStatus();

  return NextResponse.json(
    {
      status: 'success',
      message: 'Calendar connection status fetched successfully.',
      data: {
        status,
      },
    },
    { status: 200 }
  );
}
