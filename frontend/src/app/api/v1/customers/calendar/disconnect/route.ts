import { NextResponse } from 'next/server';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

export async function DELETE(): Promise<NextResponse<{ status: 'success' | 'error'; message: string }>> {
  eventStore.disconnectCalendar();

  return NextResponse.json(
    {
      status: 'success',
      message: 'Calendar disconnected successfully.',
    },
    { status: 200 }
  );
}
