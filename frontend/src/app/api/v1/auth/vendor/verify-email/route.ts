import { NextRequest } from 'next/server';

import { proxyApiRequest, shouldUseVendorAuthMock } from '@/app/api/v1/_proxy';

import { mockVendorVerifyEmail } from '../_mock';

export async function GET(request: NextRequest) {
  if (shouldUseVendorAuthMock()) {
    const token = request.nextUrl.searchParams.get('token');
    return mockVendorVerifyEmail(token);
  }

  return proxyApiRequest(request, '/auth/vendor/verify-email');
}

export async function POST(request: NextRequest) {
  if (shouldUseVendorAuthMock()) {
    const body = (await request.json()) as { token?: string };
    return mockVendorVerifyEmail(body.token ?? null);
  }

  return proxyApiRequest(request, '/auth/vendor/verify-email');
}
