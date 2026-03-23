import { NextRequest } from 'next/server';

import { proxyApiRequest, shouldUseVendorAuthMock } from '@/app/api/v1/_proxy';

import { mockVendorResetPassword } from '../_mock';

export async function POST(request: NextRequest) {
  if (shouldUseVendorAuthMock()) {
    const payload = (await request.json()) as {
      token?: string;
      password?: string;
    };

    return mockVendorResetPassword(payload);
  }

  return proxyApiRequest(request, '/auth/vendor/password/reset');
}
