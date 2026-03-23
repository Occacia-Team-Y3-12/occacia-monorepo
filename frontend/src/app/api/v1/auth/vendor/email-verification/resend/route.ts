import { NextRequest } from 'next/server';

import { proxyApiRequest, shouldUseVendorAuthMock } from '@/app/api/v1/_proxy';

import { mockVendorResendVerificationEmail } from '../../_mock';

export async function POST(request: NextRequest) {
  if (shouldUseVendorAuthMock()) {
    const body = (await request.json()) as { email?: string };
    return mockVendorResendVerificationEmail(body);
  }

  return proxyApiRequest(request, '/auth/vendor/email-verification/resend');
}
