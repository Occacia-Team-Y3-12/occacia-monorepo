import { NextRequest, NextResponse } from 'next/server';

import { proxyApiRequest } from '@/app/api/v1/_proxy';
import { featureFlags } from '@/config/featureFlags';

type RouteContext = {
  params: {
    taskId: string;
  };
};

export async function GET(
  request: NextRequest,
  { params }: RouteContext
) {
  if (!featureFlags.useVendorTasksMock) {
    return proxyApiRequest(request, `/vendors/tasks/${params.taskId}`);
  }

  const now = Date.now();

  return NextResponse.json({
    id: Number.parseInt(params.taskId, 10) || 0,
    title: 'Mock Vendor Task Detail',
    description: 'This is a mock vendor task detail response for frontend-only flows.',
    status: 'assigned',
    priority: 'medium',
    budget_min: 2200,
    budget_max: 4200,
    agreed_price: 3200,
    due_date: new Date(now + 86400000).toISOString(),
    expiry_date: null,
    completed_at: null,
    responded_at: new Date(now - 3600000).toISOString(),
    created_at: new Date(now - 2 * 86400000).toISOString(),
    customer: {
      id: 1,
      name: 'Mock Customer',
      email: 'customer@occacia.test',
    },
    event: {
      id: 1,
      title: 'Mock Celebration',
      occasion_type: 'Birthday',
      event_date: new Date(now + 2 * 86400000).toISOString(),
    },
    offering: {
      id: 1,
      name: 'Mock Premium Offering',
      category: 'Photography',
    },
    time_remaining: '23h 59m',
    can_respond: true,
  });
}
