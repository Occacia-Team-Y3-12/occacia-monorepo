import { NextResponse } from 'next/server';
import { CalendarProvidersResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

export async function GET(): Promise<NextResponse<CalendarProvidersResponse>> {
  const providers = eventStore.getCalendarProviders();

  return NextResponse.json(
    {
      status: 'success',
      message: 'Calendar providers fetched successfully.',
      data: {
        providers,
      },
    },
    { status: 200 }
  );
}
