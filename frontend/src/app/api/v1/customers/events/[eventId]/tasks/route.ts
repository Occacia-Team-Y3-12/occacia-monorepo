import { NextRequest, NextResponse } from 'next/server';
import { EventTaskMutationPayload, EventTasksResponse, EventTaskResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: {
    eventId: string;
  };
};

export async function GET(
  _request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<EventTasksResponse>> {
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

  try {
    const tasks = eventStore.getTasks(eventId);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Tasks fetched successfully.',
        data: {
          tasks,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to fetch tasks.';
    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 404 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<EventTaskResponse>> {
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

  try {
    const body = (await request.json()) as EventTaskMutationPayload;
    const title = body.title?.trim();

    if (!title) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Task title is required.',
        },
        { status: 400 }
      );
    }

    const task = eventStore.addTask(eventId, body);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Task created successfully.',
        data: {
          task,
        },
      },
      { status: 201 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to create task.';
    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 404 }
    );
  }
}
