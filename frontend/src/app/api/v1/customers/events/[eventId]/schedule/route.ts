import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { EventScheduleRequest, EventScheduleResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: Promise<{
    eventId: string;
  }>;
};

const toIso = (value: string, fallbackTime = '00:00'): string => {
  if (value.includes('T')) {
    const normalized = value.endsWith('Z') ? value : `${value}:00`;
    return new Date(normalized).toISOString();
  }
  return new Date(`${value}T${fallbackTime}:00`).toISOString();
};

export async function PUT(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<EventScheduleResponse>> {
  const { eventId } = await params;

  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${eventId}/schedule`) as Promise<NextResponse<EventScheduleResponse>>;
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
    const body = (await request.json()) as EventScheduleRequest;
    const dateTBD = Boolean(body.dateTBD);

    const startAt = !dateTBD && body.startAt ? toIso(body.startAt, '00:00') : undefined;
    const endAt = !dateTBD && body.endAt ? toIso(body.endAt, '23:59') : undefined;

    const schedule = eventStore.saveSchedule(eventId, {
      dateTBD,
      startAt,
      endAt,
      timezone: body.timezone,
      isAllDay: body.isAllDay,
      recurrence: {
        isRecurring: Boolean(body.recurrenceRule?.isRecurring),
        frequency: body.recurrenceRule?.frequency,
        interval: body.recurrenceRule?.interval,
        byDay: body.recurrenceRule?.byDay,
        endType: body.recurrenceRule?.endType || 'never',
        until: body.recurrenceRule?.until,
        count: body.recurrenceRule?.count,
      },
    });

    const clarification =
      schedule.recurrence.isRecurring && schedule.recurrence.frequency === 'yearly'
        ? 'Confirmed yearly recurrence. Keep same date each year?'
        : undefined;

    return NextResponse.json(
      {
        status: 'success',
        message: 'Schedule saved successfully.',
        data: {
          schedule,
          clarification,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to save schedule.';

    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 400 }
    );
  }
}
