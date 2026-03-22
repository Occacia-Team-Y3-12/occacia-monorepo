import { NextResponse } from 'next/server';

const sleep = (ms: number) =>
  new Promise((resolve) => setTimeout(resolve, ms));

export async function mockVendorLogin(payload: {
  email?: string;
  password?: string;
}) {
  await sleep(350);

  const isValid =
    Boolean(payload.email?.trim()) && Boolean(payload.password?.trim());

  if (!isValid) {
    return NextResponse.json(
      { message: 'Invalid credentials. Please try again.' },
      { status: 401 }
    );
  }

  return NextResponse.json({
    access_token: `mock_vendor_token_${Date.now()}`,
    token_type: 'bearer',
    role: 'VENDOR',
  });
}

export async function mockVendorRegister() {
  await sleep(350);

  return NextResponse.json({
    status: 'pending_verification',
    message: 'Please verify your email',
    data: { token: `mock_${Date.now()}` },
  });
}

export async function mockVendorForgotPassword(payload: { email?: string }) {
  await sleep(1200);

  if (!payload.email?.trim()) {
    return NextResponse.json(
      { message: 'Email is required.' },
      { status: 400 }
    );
  }

  return NextResponse.json({ ok: true });
}

export async function mockVendorResetPassword(payload: {
  token?: string;
  password?: string;
}) {
  await sleep(800);

  if (!payload.token?.startsWith('mock_')) {
    return NextResponse.json(
      { message: 'Invalid or expired reset link' },
      { status: 400 }
    );
  }

  if (!payload.password?.trim()) {
    return NextResponse.json(
      { message: 'Password is required' },
      { status: 400 }
    );
  }

  return NextResponse.json({ ok: true });
}

export async function mockVendorVerifyEmail(token: string | null) {
  await sleep(500);

  const isValid = Boolean(token && token.startsWith('mock_'));

  if (!isValid) {
    return NextResponse.json(
      {
        status: 'error',
        message: 'Invalid or expired verification token',
      },
      { status: 400 }
    );
  }

  return NextResponse.json({
    status: 'success',
    message: 'Email verified successfully',
    data: { verified: true },
  });
}
