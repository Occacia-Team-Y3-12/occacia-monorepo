import { NextRequest, NextResponse } from 'next/server';
import { proxyApiRequest, shouldUseCustomerPlanningMockApi } from '@/app/api/v1/_proxy';
import { CalendarStatusResponse } from '@/types/customerEventChat';
import { eventStore } from '@/app/api/v1/customers/_eventStore';

type ExchangeCodeRequest = {
  provider: string;
  code: string;
  state?: string;
  redirectUri: string;
};

const toProviderId = (provider: string) => {
  const normalized = provider.trim().toLowerCase();
  if (normalized === 'google' || normalized === 'apple' || normalized === 'microsoft') {
    return normalized;
  }
  return null;
};

export async function POST(request: NextRequest): Promise<NextResponse<CalendarStatusResponse>> {
  if (!shouldUseCustomerPlanningMockApi()) {
    return proxyApiRequest(request, '/customers/calendar/exchange-code') as Promise<NextResponse<CalendarStatusResponse>>;
  }

  try {
    const body = (await request.json()) as ExchangeCodeRequest;
    const provider = toProviderId(body.provider || '');

    if (!provider) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'A valid calendar provider is required.',
        },
        { status: 400 }
      );
    }

    const status = eventStore.connectCalendar(provider);

    return NextResponse.json(
      {
        status: 'success',
        message: 'Calendar connected successfully.',
        data: {
          status,
        },
      },
      { status: 200 }
    );
  } catch {
    return NextResponse.json(
      {
        status: 'error',
        message: 'Failed to complete calendar authorization.',
      },
      { status: 400 }
    );
  }
}
