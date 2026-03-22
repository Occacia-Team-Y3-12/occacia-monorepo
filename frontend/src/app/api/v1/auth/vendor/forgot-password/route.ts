import { NextRequest } from 'next/server';

import { proxyApiRequest, shouldUseVendorAuthMock } from '@/app/api/v1/_proxy';

import { mockVendorForgotPassword } from '../_mock';

export async function POST(request: NextRequest) {
  if (shouldUseVendorAuthMock()) {
    const payload = (await request.json()) as { email?: string };
    return mockVendorForgotPassword(payload);
  }

  return proxyApiRequest(request, '/auth/vendor/forgot-password');
}
