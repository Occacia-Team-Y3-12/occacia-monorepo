import { NextRequest } from 'next/server';

import { proxyApiRequest, shouldUseVendorAuthMock } from '@/app/api/v1/_proxy';

import { mockVendorRegister } from '../_mock';

export async function POST(request: NextRequest) {
  if (shouldUseVendorAuthMock()) {
    await request.json();
    return mockVendorRegister();
  }

  return proxyApiRequest(request, '/auth/vendor/register');
}
