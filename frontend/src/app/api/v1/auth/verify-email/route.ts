import { NextRequest, NextResponse } from 'next/server';

interface VerifyEmailResponse {
  status: string;
  message: string;
  data?: {
    verified: boolean;
  };
}

/**
 * GET /api/v1/auth/verify-email
 * Mock email verification endpoint
 * 
 * Accepts token as query parameter and returns verification status
 */
export async function GET(request: NextRequest): Promise<NextResponse<VerifyEmailResponse>> {
  try {
    const token = request.nextUrl.searchParams.get('token');

    // Validate token
    if (!token) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Verification token is required'
        },
        { status: 400 }
      );
    }

    // Mock validation: token must start with 'mock_' or 'token_'
    const isValid = token.startsWith('mock_') || token.startsWith('token_');

    if (!isValid) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Invalid or expired verification token'
        },
        { status: 400 }
      );
    }

    // Mock: Simulate processing delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Return success response
    return NextResponse.json(
      {
        status: 'success',
        message: 'Email verified successfully',
        data: {
          verified: true
        }
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Email verification error:', error);
    return NextResponse.json(
      {
        status: 'error',
        message: 'Email verification failed'
      },
      { status: 500 }
    );
  }
}

/**
 * POST /api/v1/auth/verify-email
 * Alternative POST endpoint for email verification (if needed)
 */
export async function POST(request: NextRequest): Promise<NextResponse<VerifyEmailResponse>> {
  try {
    const body = await request.json();
    const token = body.token || request.nextUrl.searchParams.get('token');

    if (!token) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Verification token is required'
        },
        { status: 400 }
      );
    }

    // Mock validation
    const isValid = token.startsWith('mock_') || token.startsWith('token_');

    if (!isValid) {
      return NextResponse.json(
        {
          status: 'error',
          message: 'Invalid or expired verification token'
        },
        { status: 400 }
      );
    }

    // Mock: Simulate processing delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    return NextResponse.json(
      {
        status: 'success',
        message: 'Email verified successfully',
        data: {
          verified: true
        }
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('Email verification error:', error);
    return NextResponse.json(
      {
        status: 'error',
        message: 'Email verification failed'
      },
      { status: 500 }
    );
  }
}
