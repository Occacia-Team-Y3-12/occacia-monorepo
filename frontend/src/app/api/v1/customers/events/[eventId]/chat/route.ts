import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { EventChatRequest, EventChatResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type RouteContext = {
  params: Promise<{
    eventId: string;
  }>;
};

export async function POST(
  request: NextRequest,
  { params }: RouteContext
): Promise<NextResponse<EventChatResponse>> {
  const { eventId } = await params;

  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, `/customers/events/${eventId}/chat`) as Promise<NextResponse<EventChatResponse>>;
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
    const body = (await request.json()) as EventChatRequest;
    const message = body.content?.trim() || body.message?.trim();

    if (!message) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Message is required.',
        },
        { status: 400 }
      );
    }

    eventStore.addCustomerMessage(eventId, message);
    const assistantMessage = eventStore.addAssistantMessage(eventId, message);
    const tasks = eventStore.getTasks(eventId);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Chat processed successfully.',
        data: {
          message: assistantMessage,
          suggestedTasks: tasks,
        },
      },
      { status: 200 }
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to process chat.';
    return NextResponse.json(
      {
        status: 'error',
        message,
      },
      { status: 404 }
    );
  }
}
