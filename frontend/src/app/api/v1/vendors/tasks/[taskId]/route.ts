import { NextRequest, NextResponse } from 'next/server';

import { proxyApiRequest } from '@/app/api/v1/_proxy';
import { featureFlags } from '@/config/featureFlags';
import { getMockVendorTaskDetail } from '@/mocks/vendor/vendorTaskDetail';

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

  return NextResponse.json(getMockVendorTaskDetail(params.taskId));
}
