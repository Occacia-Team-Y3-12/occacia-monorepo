import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { EventTaskResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: {
    eventId: string;
    taskId: string;
  };
};

export async function PUT(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<EventTaskResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${params.eventId}/tasks/${params.taskId}`) as Promise<NextResponse<EventTaskResponse>>;
  }

  const { eventId, taskId } = params;

  if (!eventId || !taskId) {
    return NextResponse.json(
      {
        status: 'error',
        message: 'Event id and task id are required.',
      },
      { status: 400 }
    );
  }

  try {
    const body = (await request.json()) as { title?: string; description?: string; needsVendor?: boolean; category?: string; completed?: boolean };

    if (typeof body.title === 'string' && body.title.trim().length === 0) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Task title cannot be empty.',
        },
        { status: 400 }
      );
    }

    const task = eventStore.updateTask(eventId, taskId, body);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Task updated successfully.',
        data: {
          task,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to update task.';
    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 404 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<{ status: 'success' | 'error'; message: string }>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${params.eventId}/tasks/${params.taskId}`) as Promise<NextResponse<{ status: 'success' | 'error'; message: string }>>;
  }

  const { eventId, taskId } = params;

  if (!eventId || !taskId) {
    return NextResponse.json(
      {
        status: 'error',
        message: 'Event id and task id are required.',
      },
      { status: 400 }
    );
  }

  try {
    eventStore.deleteTask(eventId, taskId);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Task deleted successfully.',
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to delete task.';
    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 404 }
    );
  }
}
